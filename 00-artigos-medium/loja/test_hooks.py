"""Testa os hooks na mão, sem Claude Code: simula o JSON que ele enviaria pelo stdin.

Uso:  python test_hooks.py
"""
import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HOOKS = Path(__file__).parent / ".claude" / "hooks"

# o guard grava decisions.jsonl; nos testes isso vai para uma pasta temporária, não para o seu .claude/logs
GUARD_ROOT = tempfile.mkdtemp(prefix="harness-guard-")
atexit.register(shutil.rmtree, GUARD_ROOT, True)
G = {"CLAUDE_PROJECT_DIR": GUARD_ROOT}


def run(script, payload, env=None, raw=None):
    stdin = raw if raw is not None else json.dumps(payload, ensure_ascii=False)
    return subprocess.run([sys.executable, str(HOOKS / script)], input=stdin, text=True,
                          encoding="utf-8", errors="replace", capture_output=True,
                          env={**os.environ, **(env or {})})


def guard(tool, **tool_input):
    return run("guard.py", {"tool_name": tool, "tool_input": tool_input}, G)


def check(name, ok):
    print(("OK   " if ok else "FALHOU"), name)
    if not ok:
        sys.exit(1)


# ---- guard.py (PreToolUse) ----
r = guard("Edit", file_path="C:\\proj\\src\\Loja.Infrastructure\\Migrations\\20260101_Init.cs")
check("bloqueia Edit em Migrations (caminho Windows)", r.returncode == 2 and "Migrations" in r.stderr)
r = guard("Write", file_path="/proj/src/Loja.Api/appsettings.Production.json")
check("bloqueia Write em appsettings.Production.json", r.returncode == 2)
r = guard("Edit", file_path="/proj/src/Loja.Domain/Pedido.cs")
check("libera Edit em arquivo comum", r.returncode == 0)
r = guard("Bash", command="rm -rf bin obj")
check("bloqueia rm -rf", r.returncode == 2 and "rm -rf" in r.stderr)
r = guard("Bash", command="git push origin main --force")
check("bloqueia git push --force", r.returncode == 2)
r = guard("PowerShell", command="Remove-Item -Recurse -Force bin")
check("bloqueia Remove-Item -Recurse (ferramenta PowerShell)", r.returncode == 2)
r = guard("Bash", command="dotnet build")
check("libera dotnet build", r.returncode == 0)
r = run("guard.py", None, G, raw="isto não é json")
check("fail-closed com entrada quebrada", r.returncode == 2)

# ---- encoding: console ANSI do Windows (emulado com PYTHONIOENCODING=cp1252) ----
WIN = {**G, "PYTHONIOENCODING": "cp1252"}
r = run("guard.py", {"tool_name": "Write", "tool_input": {"file_path": "C:\\proj\\Migrations\\x.cs"}}, WIN)
check("mensagem de bloqueio sai em UTF-8, com acentos legíveis", r.returncode == 2 and "é protegido" in r.stderr)
r = run("guard.py", {"tool_name": "Edit", "tool_input": {"file_path": "C:\\proj\\ÁREA\\Pedido.cs"}}, WIN)
check("caminho com acento não gera falso bloqueio", r.returncode == 0)

# ---- decisions.jsonl do guard: só os bloqueios, nunca as liberações ----
linhas = [json.loads(l) for l in
          Path(GUARD_ROOT, ".claude", "logs", "decisions.jsonl").read_text(encoding="utf-8").splitlines()]
check("guard registra cada bloqueio (7) e só eles",
      len(linhas) == 7 and all(l["hook"] == "guard" and l["decision"] == "block" for l in linhas))
check("registro traz a regra violada e o alvo",
      {l["rule"] for l in linhas} == {"arquivo protegido", "rm -rf", "git push --force",
                                      "Remove-Item -Recurse", "entrada ilegível"}
      and any("Migrations" in l.get("target", "") for l in linhas))
check("liberações não entram no registro", not any("Pedido.cs" in l.get("target", "") for l in linhas))

# falha ao gravar o log nunca muda a decisão ('.claude' é um arquivo, então o mkdir do log falha)
quebrado = tempfile.mkdtemp(prefix="harness-quebrado-")
Path(quebrado, ".claude").write_text("x")
r = run("guard.py", {"tool_name": "Bash", "tool_input": {"command": "rm -rf bin"}}, {"CLAUDE_PROJECT_DIR": quebrado})
check("erro ao gravar o log não afrouxa o bloqueio do guard", r.returncode == 2)
shutil.rmtree(quebrado, ignore_errors=True)

# ---- verify_done.py (Stop) ----
with tempfile.TemporaryDirectory() as repo:
    git = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)
    git("init", "-q"); git("config", "user.email", "a@b.c"); git("config", "user.name", "t")
    Path(repo, "Pedido.cs").write_text("class Pedido {}\n")
    git("add", "."); git("commit", "-qm", "init")
    session = f"teste-{uuid.uuid4().hex[:8]}"
    payload = {"session_id": session, "cwd": repo}
    # HARNESS_TEST_CMD é dividido por espaços; usamos scripts para evitar aspas.
    fail_script = Path(repo).parent / f"{session}_fail.py"
    fail_script.write_text("print('Failed PedidoTests.Total'); raise SystemExit(1)\n")
    pass_script = Path(repo).parent / f"{session}_pass.py"
    pass_script.write_text("raise SystemExit(0)\n")
    FAIL = {"HARNESS_TEST_CMD": f"{sys.executable} {fail_script}"}
    PASS = {"HARNESS_TEST_CMD": f"{sys.executable} {pass_script}"}

    r = run("verify_done.py", payload, FAIL)
    check("sem mudança em .cs: não roda testes e libera", r.returncode == 0 and r.stdout == "")
    Path(repo, "Pedido.cs").write_text("class Pedido { int x; }\n")
    Path(repo, "Nova").mkdir(); Path(repo, "Nova", "Item.cs").write_text("class Item {}\n")
    git("checkout", "--", "Pedido.cs")
    r = run("verify_done.py", payload, FAIL)
    check("arquivo .cs novo em PASTA NOVA também dispara os testes", "decision" in r.stdout)
    Path(repo, "Nova", "Item.cs").unlink(); Path(repo, "Nova").rmdir()
    Path(repo, "Pedido.cs").write_text("class Pedido { int x; }\n")
    (Path(tempfile.gettempdir()) / f"harness-stop-{session}").unlink(missing_ok=True)
    r = run("verify_done.py", payload, PASS)
    check("testes passam: libera", r.returncode == 0 and r.stdout == "")
    r = run("verify_done.py", payload, FAIL)
    check("tentativa 1: bloqueia com o motivo", json.loads(r.stdout)["decision"] == "block"
          and "1/3" in json.loads(r.stdout)["reason"])
    r = run("verify_done.py", payload, FAIL)
    check("tentativa 2: bloqueia", json.loads(r.stdout)["decision"] == "block")
    r = run("verify_done.py", payload, FAIL)
    check("tentativa 3: desiste e avisa o humano", "systemMessage" in json.loads(r.stdout))
    entradas = [json.loads(l) for l in
                Path(repo, ".claude", "logs", "decisions.jsonl").read_text(encoding="utf-8").splitlines()]
    check("decisions.jsonl conta a história do portão: skip, block, allow, block, block, give_up",
          [e["decision"] for e in entradas] == ["skip", "block", "allow", "block", "block", "give_up"]
          and [e.get("attempt") for e in entradas] == [None, 1, None, 1, 2, 3])
    check("cada rodada de testes registra a duração", all("duration_s" in e for e in entradas[1:]))
    fail_script.unlink(); pass_script.unlink()

    # ---- trace.py (PostToolUse) ----
    r = run("trace.py", {"session_id": session, "cwd": repo, "tool_name": "Edit",
                         "tool_input": {"file_path": "/proj/Pedido.cs"}})
    log = Path(repo, ".claude", "logs", "tool-calls.jsonl")
    check("trace grava uma linha JSON por ação", r.returncode == 0 and json.loads(log.read_text())["tool"] == "Edit")
    run("trace.py", {"session_id": session, "cwd": repo, "tool_name": "Grep", "tool_input": {"pattern": "Total"}})
    check("trace usa o padrão do Grep como alvo", json.loads(log.read_text().splitlines()[-1])["target"] == "Total")

# ---- falha ao gravar o log não pode afrouxar o portão ----
with tempfile.TemporaryDirectory() as repo:
    git = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)
    git("init", "-q"); git("config", "user.email", "a@b.c"); git("config", "user.name", "t")
    Path(repo, "A.cs").write_text("class A {}\n"); git("add", "."); git("commit", "-qm", "init")
    Path(repo, "A.cs").write_text("class A { int x; }\n")
    Path(repo, ".claude").write_text("x")                      # '.claude' como arquivo: o mkdir do log falha
    session = f"log-{uuid.uuid4().hex[:8]}"
    fail = Path(repo).parent / f"{session}_fail.py"
    fail.write_text("raise SystemExit(1)\n")
    env = {"HARNESS_TEST_CMD": f"{sys.executable} {fail}", "CLAUDE_PROJECT_DIR": repo}
    r = run("verify_done.py", {"session_id": session, "cwd": repo}, env)
    check("erro ao gravar o log não afrouxa o portão do Stop", r.returncode == 0 and "decision" in r.stdout)
    fail.unlink()

# ---- saída de teste fora de UTF-8 não pode derrubar o portão ----
with tempfile.TemporaryDirectory() as repo:
    git = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)
    git("init", "-q"); git("config", "user.email", "a@b.c"); git("config", "user.name", "t")
    Path(repo, "A.cs").write_text("class A {}\n"); git("add", "."); git("commit", "-qm", "init")
    Path(repo, "A.cs").write_text("class A { int x; }\n")
    session = f"enc-{uuid.uuid4().hex[:8]}"
    bad = Path(repo).parent / f"{session}_bad.py"
    bad.write_text("import sys\nsys.stdout.buffer.write(b'Falhou \\x81\\x8d\\x8f\\x90\\x9d\\n')\nraise SystemExit(1)\n")
    env = {"HARNESS_TEST_CMD": f"{sys.executable} {bad}", "CLAUDE_PROJECT_DIR": repo}
    r = run("verify_done.py", {"session_id": session, "cwd": repo}, env)
    check("saída de teste com bytes inválidos ainda bloqueia (não cai aberto)",
          r.returncode == 0 and "decision" in r.stdout)
    bad.unlink()

# ---- saída UTF-8 do teste chega legível, mesmo com locale não-UTF-8 (ex.: cp1252 no Windows) ----
with tempfile.TemporaryDirectory() as repo:
    git = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)
    git("init", "-q"); git("config", "user.email", "a@b.c"); git("config", "user.name", "t")
    Path(repo, "A.cs").write_text("class A {}\n"); git("add", "."); git("commit", "-qm", "init")
    Path(repo, "A.cs").write_text("class A { int x; }\n")
    session = f"u8-{uuid.uuid4().hex[:8]}"
    u8 = Path(repo).parent / f"{session}_u8.py"
    u8.write_text("import sys\nsys.stdout.buffer.write('Execução de teste → Com falha – 1\\n'.encode('utf-8'))\nraise SystemExit(1)\n",
                  encoding="utf-8")
    env = {"HARNESS_TEST_CMD": f"{sys.executable} {u8}", "CLAUDE_PROJECT_DIR": repo,
           "LC_ALL": "C", "PYTHONUTF8": "0", "PYTHONCOERCECLOCALE": "0"}   # locale não-UTF-8 (emula o Windows)
    r = run("verify_done.py", {"session_id": session, "cwd": repo}, env)
    check("saída UTF-8 do dotnet chega legível ao agente (sem 'ExecuÃ§Ã£o')",
          "Execução de teste → Com falha – 1" in json.loads(r.stdout)["reason"])
    u8.unlink()

# ---- projeto dentro de um repo maior (ex.: engineering-lab/00-artigos-medium/loja) ----
with tempfile.TemporaryDirectory() as repo:
    git = lambda *a: subprocess.run(["git", *a], cwd=repo, capture_output=True, check=True)
    git("init", "-q"); git("config", "user.email", "a@b.c"); git("config", "user.name", "t")
    proj = Path(repo, "artigos", "loja"); proj.mkdir(parents=True)
    other = Path(repo, "outro-projeto"); other.mkdir()
    (proj / "Pedido.cs").write_text("class Pedido {}\n"); (other / "Outro.cs").write_text("class O {}\n")
    git("add", "."); git("commit", "-qm", "init")
    session = f"mono-{uuid.uuid4().hex[:8]}"
    fail_script = Path(repo).parent / f"{session}_fail.py"
    fail_script.write_text("raise SystemExit(1)\n")
    env = {"HARNESS_TEST_CMD": f"{sys.executable} {fail_script}", "CLAUDE_PROJECT_DIR": str(proj)}
    payload = {"session_id": session, "cwd": repo}          # cwd "errado" de propósito
    (other / "Outro.cs").write_text("class O { int y; }\n")
    r = run("verify_done.py", payload, env)
    check("mudança em OUTRO projeto do repo não dispara os testes da Loja", r.stdout == "" and r.returncode == 0)
    (proj / "Pedido.cs").write_text("class Pedido { int x; }\n")
    r = run("verify_done.py", payload, env)
    check("mudança dentro da Loja dispara (usa CLAUDE_PROJECT_DIR, não o cwd)", "decision" in r.stdout)
    fail_script.unlink()
    r = run("trace.py", {"session_id": session, "cwd": repo, "tool_name": "Edit",
                         "tool_input": {"file_path": "x.cs"}}, {"CLAUDE_PROJECT_DIR": str(proj)})
    check("trace grava dentro da pasta do projeto", (proj / ".claude" / "logs" / "tool-calls.jsonl").exists())

print("\nTodos os testes dos hooks passaram.")
