"""PreToolUse: bloqueia o que o harness não quer deixar o agente executar."""
import json
import re
import sys

PROTECTED = ("/Migrations/", "appsettings.Production.json", "/.github/workflows/")
DANGEROUS = [
    (r"\brm\s+-rf?\b", "rm -rf", "Apague arquivos específicos, um a um."),
    (r"git\s+push\b.*--force", "git push --force", "Use um push normal ou peça ajuda humana."),
    (r"dotnet\s+ef\s+database\s+drop", "ef database drop", "Nunca derrube o banco. Crie uma migration."),
    (r"(?i)remove-item\b.*-recurse", "Remove-Item -Recurse", "Apague arquivos específicos, um a um."),
]

def block(message: str):
    print(message, file=sys.stderr)  # o que vai para stderr é o que o agente lê
    sys.exit(2)                      # exit 2 bloqueia. exit 1 NÃO bloqueia


try:
    data = json.load(sys.stdin)
except Exception:  # fail-closed: um guarda quebrado não pode virar um guarda desligado
    block("guard.py não conseguiu ler a entrada do hook. Bloqueado por segurança.")

tool = data.get("tool_name")
tool_input = data.get("tool_input", {})

if tool in ("Edit", "Write"):
    path = tool_input.get("file_path", "").replace("\\", "/")  # Windows manda barra invertida
    if any(p in path for p in PROTECTED):
        block(f"Bloqueado: '{path}' é protegido. Migrations são geradas por "
              "`dotnet ef migrations add <Nome>`, nunca editadas à mão; "
              "workflows e appsettings de produção exigem revisão humana.")

if tool in ("Bash", "PowerShell"):   # PowerShell: Windows sem Git for Windows
    command = tool_input.get("command", "")
    for pattern, label, hint in DANGEROUS:
        if re.search(pattern, command):
            block(f"Bloqueado: `{label}` não é permitido neste projeto. {hint}")

sys.exit(0)  # sem opinião: segue o fluxo normal de permissões