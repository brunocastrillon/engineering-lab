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