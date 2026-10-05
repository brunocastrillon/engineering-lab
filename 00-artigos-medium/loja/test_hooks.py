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