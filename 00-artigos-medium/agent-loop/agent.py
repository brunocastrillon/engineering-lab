"""agent.py — um agente de manutenção de código: loop + memória + guardrails + observabilidade."""
import json
import locale
import shlex
import subprocess
import sys
import time
import uuid
from pathlib import Path

import anthropic

MODEL = "claude-sonnet-5-5"
MAX_STEPS = 15           # parada nº 1: orçamento de passos
MAX_REPEATS = 3          # parada nº 2: a mesma chamada repetida = sem progresso
MAX_VERIFY_RETRIES = 2   # quantas vezes o harness recusa um "terminei"

ROOT = Path(__file__).parent
WORKDIR = (ROOT / "workspace").resolve()
SKILL = ROOT / "skills" / "fix_bug.md"            # memória procedural
EPISODES = ROOT / "memory" / "episodes.jsonl"     # memória episódica
TRACES = ROOT / "traces"                          # observabilidade
ALLOWED = {"pytest": [sys.executable, "-m", "pytest"]}   # policy: só o que está na lista

TOOLS = [
    {"name": "list_files", "description": "Lista os arquivos do workspace.",
     "input_schema": {"type": "object", "properties": {}}},
    {"name": "read_file", "description": "Lê um arquivo do workspace.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}},
                      "required": ["path"]}},
    {"name": "write_file", "description": "Sobrescreve um arquivo do workspace.",
     "input_schema": {"type": "object",
                      "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                      "required": ["path", "content"]}},
    {"name": "run_command", "description": "Executa um comando permitido (ex.: pytest) no workspace.",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}},
                      "required": ["command"]}},
]


# ---------- tools + guardrails ----------
def decode(raw: bytes) -> str:
    """pytest pode emitir UTF-8 ou a codepage do Windows; nunca deixe isso derrubar o agente."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode(locale.getpreferredencoding(False), errors="replace")



def safe_path(rel: str) -> Path:
    path = (WORKDIR / rel).resolve()
    if path != WORKDIR and WORKDIR not in path.parents:
        raise PermissionError(f"'{rel}' está fora do workspace.")
    return path


def run_tool(name: str, args: dict) -> str:
    if name == "list_files":
        files = (p.relative_to(WORKDIR) for p in sorted(WORKDIR.rglob("*")) if p.is_file())
        return "\n".join(str(f) for f in files if not any(x.startswith((".", "__")) for x in f.parts))
    if name == "read_file":
        return safe_path(args["path"]).read_text(encoding="utf-8")
    if name == "write_file":
        safe_path(args["path"]).write_text(args["content"], encoding="utf-8")
        return f"{args['path']} gravado."
    if name == "run_command":
        argv = shlex.split(args["command"])
        if not argv or argv[0] not in ALLOWED:
            raise PermissionError(f"Comando não permitido. Permitidos: {sorted(ALLOWED)}")
        done = subprocess.run(ALLOWED[argv[0]] + argv[1:], cwd=WORKDIR,
                              capture_output=True, timeout=60)
        return (decode(done.stdout) + decode(done.stderr))[-3000:]
    raise ValueError(f"Tool desconhecida: {name}")


# ---------- memória ----------
def build_system() -> str:
    skill = SKILL.read_text(encoding="utf-8") if SKILL.exists() else "(nenhuma)"
    past = "(nenhum)"
    if EPISODES.exists():
        last = EPISODES.read_text(encoding="utf-8").strip().splitlines()[-3:]
        past = "\n".join("- " + json.loads(line)["summary"] for line in last)
    return ("Você é um agente de manutenção de código. Trabalhe só dentro do workspace.\n\n"
            f"## Procedimento\n{skill}\n\n## Episódios recentes\n{past}")


def save_episode(task: str, outcome: str, steps: int) -> None:
    EPISODES.parent.mkdir(exist_ok=True)
    record = {"ts": time.time(), "summary": f"{task} -> {outcome} ({steps} passos)"}
    with EPISODES.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------- observabilidade ----------
class Trace:
    def __init__(self):
        TRACES.mkdir(exist_ok=True)
        self.run_id = uuid.uuid4().hex[:8]
        self.path = TRACES / f"{self.run_id}.jsonl"

    def log(self, event: str, **data) -> None:
        record = {"t": round(time.time(), 2), "event": event, **data}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ---------- verificação independente ----------
def verify() -> tuple[bool, str]:
    try:
        done = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=WORKDIR,
                              capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:          # teste travado também é teste reprovado
        return False, "A verificação estourou o tempo limite (60 s)."
    return done.returncode == 0, (decode(done.stdout) + decode(done.stderr))[-1500:]


def text_of(response) -> str:
    return "".join(b.text for b in response.content if b.type == "text")


# ---------- o loop ----------
def run(task: str, client=None) -> tuple[bool, str]:
    client = client or anthropic.Anthropic()
    trace = Trace()
    messages = [{"role": "user", "content": task}]
    seen: dict = {}
    verify_retries = 0

    for step in range(1, MAX_STEPS + 1):
        response = client.messages.create(model=MODEL, max_tokens=2048, system=build_system(),
                                          tools=TOOLS, messages=messages)
        trace.log("model", step=step, stop_reason=response.stop_reason)
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "tool_use":
            results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                key = (block.name, json.dumps(block.input, sort_keys=True))
                seen[key] = seen.get(key, 0) + 1
                try:
                    if seen[key] > MAX_REPEATS:
                        raise RuntimeError("Chamada repetida sem progresso. Mude de estratégia.")
                    output, failed = run_tool(block.name, block.input), False
                except Exception as exc:       # o erro volta para o modelo; o loop não cai
                    output, failed = f"{type(exc).__name__}: {exc}", True
                trace.log("tool", step=step, tool=block.name, error=failed)
                result = {"type": "tool_result", "tool_use_id": block.id, "content": output}
                if failed:
                    result["is_error"] = True
                results.append(result)
            messages.append({"role": "user", "content": results})
            continue

        if response.stop_reason == "end_turn":
            ok, report = verify()               # não confie em "terminei": confira
            trace.log("verify", step=step, ok=ok)
            if ok or verify_retries >= MAX_VERIFY_RETRIES:
                save_episode(task, "sucesso" if ok else "testes ainda vermelhos", step)
                return ok, text_of(response)
            verify_retries += 1
            messages.append({"role": "user", "content":
                             f"Verificação independente: os testes ainda falham.\n{report}\nContinue."})
            continue

        trace.log("abort", step=step, reason=response.stop_reason)
        save_episode(task, f"abortado ({response.stop_reason})", step)
        return False, f"Parado: {response.stop_reason}"

    trace.log("budget_exhausted", steps=MAX_STEPS)
    save_episode(task, "orçamento esgotado", MAX_STEPS)
    return False, "Orçamento de passos esgotado."


if __name__ == "__main__":
    ok, final = run(sys.argv[1] if len(sys.argv) > 1 else "Faça o pytest passar.")
    print("OK" if ok else "FALHOU", "-", final)
