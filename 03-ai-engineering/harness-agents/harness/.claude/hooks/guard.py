#!/usr/bin/env python3
"""PreToolUse: bloqueia o que o harness não quer deixar o agente executar."""
import json
import os
import re
import sys
import time
from pathlib import Path

# No Windows, stdin/stderr usam a codepage ANSI, mas o Claude Code fala UTF-8.
sys.stdin.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

PROTECTED = ("/Migrations/", "appsettings.Production.json", "/.github/workflows/")
DANGEROUS = [
    (r"\brm\s+-rf?\b", "rm -rf", "Para limpar artefatos de build use `dotnet clean`. Para o resto, apague só arquivos específicos."),
    (r"git\s+push\b.*--force", "git push --force", "Use um push normal ou peça ajuda humana."),
    (r"dotnet\s+ef\s+database\s+drop", "ef database drop", "Nunca derrube o banco. Crie uma migration."),
    (r"(?i)remove-item\b.*-recurse", "Remove-Item -Recurse", "Para limpar artefatos de build use `dotnet clean`. Para o resto, apague só arquivos específicos."),
]

data = {}


def registrar(**campos):
    """Anota a decisão em .claude/logs/decisions.jsonl. Falha de log nunca muda a decisão."""
    try:
        root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
        log = Path(root) / ".claude" / "logs" / "decisions.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        entrada = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "session": data.get("session_id"),
                   "hook": "guard", **campos}
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    except Exception:
        pass


def block(message: str, **campos):
    registrar(decision="block", **campos)
    print(message, file=sys.stderr)  # o que vai para stderr é o que o agente lê
    sys.exit(2)                      # exit 2 bloqueia. exit 1 NÃO bloqueia


try:
    data = json.load(sys.stdin)
except Exception:  # fail-closed: um guarda quebrado não pode virar um guarda desligado
    block("guard.py não conseguiu ler a entrada do hook. Bloqueado por segurança.",
          rule="entrada ilegível")

tool = data.get("tool_name")
tool_input = data.get("tool_input", {})

if tool in ("Edit", "Write"):
    path = tool_input.get("file_path", "").replace("\\", "/")  # Windows manda barra invertida
    if any(p in path for p in PROTECTED):
        block(f"Bloqueado: '{path}' é protegido. Migrations são geradas por "
              "`dotnet ef migrations add <Nome>`, nunca editadas à mão; "
              "workflows e appsettings de produção exigem revisão humana.",
              tool=tool, rule="arquivo protegido", target=path)

if tool in ("Bash", "PowerShell"):   # PowerShell: Windows sem Git for Windows
    command = tool_input.get("command", "")
    for pattern, label, hint in DANGEROUS:
        if re.search(pattern, command):
            block(f"Bloqueado: `{label}` não é permitido neste projeto. {hint}",
                  tool=tool, rule=label, target=command[:200])

sys.exit(0)  # sem opinião: segue o fluxo normal de permissões
