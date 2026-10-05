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