#!/usr/bin/env python3
"""Stop: o agente só encerra se os testes passarem (máximo de 3 tentativas)."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# No Windows, stdin/stderr usam a codepage ANSI, mas o Claude Code fala UTF-8.
sys.stdin.reconfigure(encoding="utf-8")

TEST_CMD = os.environ.get("HARNESS_TEST_CMD", "dotnet test --nologo -v q").split()
MAX_ATTEMPTS = 3

data = json.load(sys.stdin)
# raiz do projeto (a pasta onde está o .claude), não o diretório atual do Claude
root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd", ".")
counter = Path(tempfile.gettempdir()) / f"harness-stop-{data.get('session_id', 'x')}"


def touched_csharp() -> bool:
    # -uall: lista cada arquivo novo, mesmo dentro de pastas que o git ainda não conhece
    out = subprocess.run(["git", "status", "--porcelain", "-uall", "--", "."],  # "-- ." = só esta pasta
                         capture_output=True, text=True, errors="replace", cwd=root).stdout
    return any(line.rstrip().rstrip('"').endswith(".cs") for line in out.splitlines())


if not touched_csharp():          # só conversou? não gaste tempo rodando testes
    sys.exit(0)

# errors="replace": saída fora do encoding esperado não pode derrubar o portão
result = subprocess.run(TEST_CMD, capture_output=True, text=True, errors="replace", cwd=root)
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
tail = "\n".join((result.stdout + result.stderr).splitlines()[-40:])
print(json.dumps({"decision": "block",
                  "reason": f"Os testes falharam (tentativa {attempts}/{MAX_ATTEMPTS}). "
                            f"Corrija antes de encerrar.\n\n{tail}"}))
