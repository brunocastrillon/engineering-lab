"""Testa os hooks na mão, sem Claude Code: simula o JSON que ele enviaria pelo stdin.

Uso:  python test_hooks.py
"""
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HOOKS = Path(__file__).parent / ".claude" / "hooks"

def run(script, payload, env=None, raw=None):
    stdin = raw if raw is not None else json.dumps(payload)
    return subprocess.run([sys.executable, str(HOOKS / script)], input=stdin, text=True,
                          capture_output=True, env={**os.environ, **(env or {})})

def guard(tool, **tool_input):
    return run("guard.py", {"tool_name": tool, "tool_input": tool_input})

def check(name, ok):
    print(("OK   " if ok else "FALHOU"), name)
    if not ok:
        sys.exit(1)


# --- PreToolUse ----
r = guard("Edit", file_path="..\\src\\Loja.Infrastructure\\Migrations\\20260101_Init.cs")
check("bloqueia Edit em Migrations (caminho Windows)", r.returncode == 2 and "Migrations" in r.stderr)

r = guard("Write", file_path="../src/Loja.Api/appsettings.Production.json")
check("bloqueia Write em appsettings.Production.json", r.returncode == 2)

r = guard("Edit", file_path="../src/Loja.Domain/Pedido.cs")
check("libera Edit em arquivo comum", r.returncode == 0)

r = guard("Bash", command="rm -rf bin obj")
check("bloqueia rm -rf", r.returncode == 2 and "rm -rf" in r.stderr)

r = guard("Bash", command="git push origin main --force")
check("bloqueia git push --force", r.returncode == 2)

r = guard("PowerShell", command="Remove-Item -Recurse -Force bin")
check("bloqueia Remove-Item -Recurse (ferramenta PowerShell)", r.returncode == 2)

r = guard("Bash", command="dotnet build")
check("libera dotnet build", r.returncode == 0)

r = run("guard.py", None, raw="isto não é json")
check("fail-closed com entrada quebrada", r.returncode == 2)


# ---- Stop ----
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
    fail_script.unlink(); pass_script.unlink()

    # ---- PostToolUse ----
    r = run("trace.py", {"session_id": session, "cwd": repo, "tool_name": "Edit",
                         "tool_input": {"file_path": "/proj/Pedido.cs"}})
    log = Path(repo, ".claude", "logs", "tool-calls.jsonl")
    check("trace grava uma linha JSON por ação", r.returncode == 0 and json.loads(log.read_text())["tool"] == "Edit")


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