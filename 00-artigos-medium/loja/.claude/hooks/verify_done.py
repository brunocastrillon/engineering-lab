#!/usr/bin/env python3
"""Stop: o agente só encerra se os testes passarem (máximo de 3 tentativas)."""
import json
import locale
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# No Windows, stdin/stderr usam a codepage ANSI, mas o Claude Code fala UTF-8.
sys.stdin.reconfigure(encoding="utf-8")

TEST_CMD = os.environ.get("HARNESS_TEST_CMD", "dotnet test --nologo -v q").split()
MAX_ATTEMPTS = 3


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


def touched_csharp() -> bool:
    # -uall: lista cada arquivo novo, mesmo dentro de pastas que o git ainda não conhece
    out = subprocess.run(["git", "status", "--porcelain", "-uall", "--", "."],  # "-- ." = só esta pasta
                         capture_output=True, cwd=root).stdout
    return any(line.rstrip().rstrip('"').endswith(".cs") for line in decode(out).splitlines())


if not touched_csharp():          # só conversou? não gaste tempo rodando testes
    sys.exit(0)

# bytes + decode(): saída em encoding inesperado não pode derrubar o portão
result = subprocess.run(TEST_CMD, capture_output=True, cwd=root)
if result.returncode == 0:
    counter.unlink(missing_ok=True)
    sys.exit(0)

attempts = int(counter.read_text()) + 1 if counter.exists() else 1
if attempts >= MAX_ATTEMPTS:      # desiste com transparência: escala para o humano
    counter.unlink(missing_ok=True)
    print(json.dumps({"systemMessage":
          f"Harness: os testes continuam falhando após {attempts} tentativas. Revisão humana necessária."}))
    sys.exit(0)

counter.write_text(str(attempts))
tail = "\n".join((decode(result.stdout) + decode(result.stderr)).splitlines()[-40:])
print(json.dumps({"decision": "block",
                  "reason": f"Os testes falharam (tentativa {attempts}/{MAX_ATTEMPTS}). "
                            f"Corrija antes de encerrar.\n\n{tail}"}))
