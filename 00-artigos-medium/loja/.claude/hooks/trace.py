#!/usr/bin/env python3
"""PostToolUse: registra cada ação do agente em .claude/logs/tool-calls.jsonl."""
import json
import os
import time
from pathlib import Path
import sys

data = json.load(sys.stdin)
tool_input = data.get("tool_input", {})
entry = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "session": data.get("session_id"),
    "tool": data.get("tool_name"),
    "target": str(tool_input.get("file_path") or tool_input.get("command") or "")[:200],
}
root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd", ".")
log = Path(root) / ".claude" / "logs" / "tool-calls.jsonl"
log.parent.mkdir(parents=True, exist_ok=True)
with log.open("a", encoding="utf-8") as f:
    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
