#!/usr/bin/env python3
"""Stop: recusa o encerramento (até 2 vezes) se os testes falharem; na 3ª tentativa libera e avisa o humano.

Por padrão só roda quando algum .cs mudou no git. Com `--always`, roda a cada tentativa de encerrar."""
import json
import locale
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# No Windows, stdin/stderr usam a codepage ANSI, mas o Claude Code fala UTF-8.
sys.stdin.reconfigure(encoding="utf-8")

TEST_CMD = os.environ.get("HARNESS_TEST_CMD", "dotnet test --nologo -v q").split()
MAX_REFUSALS = 2                       # recusa 2 vezes; na 3ª tentativa libera
ALWAYS = "--always" in sys.argv[1:]    # modo que também enxerga vermelho herdado


def decode(raw: bytes) -> str:
    """dotnet/git emitem UTF-8; se vier outra coisa, cai no ANSI do sistema sem nunca quebrar."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode(locale.getpreferredencoding(False), errors="replace")


data = json.load(sys.stdin)
# raiz do projeto (a pasta onde está o .claude), não o diretório atual do Claude
root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd", ".")
counter = Path(tempfile.gettempdir()) / f"harness-stop-{data.get('session_id', 'x')}"


def registrar(decision: str, **campos):
    """Anota a decisão em .claude/logs/decisions.jsonl. Falha de log nunca muda a decisão."""
    try:
        log = Path(root) / ".claude" / "logs" / "decisions.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        entrada = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "session": data.get("session_id"),
                   "hook": "verify_done", "decision": decision, **campos}
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    except Exception:
        pass


def touched_csharp() -> bool:
    # -uall: lista cada arquivo novo, mesmo dentro de pastas que o git ainda não conhece
    out = subprocess.run(["git", "status", "--porcelain", "-uall", "--", "."],  # "-- ." = só esta pasta
                         capture_output=True, cwd=root).stdout
    return any(line.rstrip().rstrip('"').endswith(".cs") for line in decode(out).splitlines())


if not ALWAYS and not touched_csharp():   # só conversou? não gaste tempo rodando testes
    registrar("skip", reason="nenhum .cs alterado")
    sys.exit(0)

# bytes + decode(): saída em encoding inesperado não pode derrubar o portão
inicio = time.monotonic()
result = subprocess.run(TEST_CMD, capture_output=True, cwd=root)
duration_s = round(time.monotonic() - inicio, 1)
if result.returncode == 0:
    counter.unlink(missing_ok=True)
    registrar("allow", duration_s=duration_s)
    sys.exit(0)

attempts = int(counter.read_text()) + 1 if counter.exists() else 1
if attempts > MAX_REFUSALS:       # desiste com transparência: libera e escala para o humano
    counter.unlink(missing_ok=True)
    registrar("give_up", attempt=attempts, duration_s=duration_s)
    print(json.dumps({"systemMessage":
          f"Harness: os testes continuam falhando e o agente já foi recusado {MAX_REFUSALS} vezes. "
          "Encerramento liberado: revisão humana necessária."}))
    sys.exit(0)

counter.write_text(str(attempts))
registrar("block", attempt=attempts, duration_s=duration_s)
tail = "\n".join((decode(result.stdout) + decode(result.stderr)).splitlines()[-40:])
if attempts == MAX_REFUSALS:
    aviso = (f"Os testes falharam (recusa {attempts} de {MAX_REFUSALS}, a última). Corrija antes de encerrar; "
             "se não conseguir, explique ao usuário o que falta em vez de insistir.")
else:
    aviso = f"Os testes falharam (recusa {attempts} de {MAX_REFUSALS}). Corrija antes de encerrar."
print(json.dumps({"decision": "block", "reason": f"{aviso}\n\n{tail}"}))
