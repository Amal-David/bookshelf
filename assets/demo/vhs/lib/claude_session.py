#!/usr/bin/env python3
"""Staged agent-session replay for a VHS launch recording.

Prints a Claude Code-style transcript at reading pace while piping real
event JSON into the actual shared ambient hook (hooks/ambient.py) — the
quote on screen is genuine hook output, only the session pacing is staged.

Requires `source lib/record_env.sh` first: it isolates HOME and opts the
scratch config into ambient delivery so the staged session's fifth tool
call (the default cadence) surfaces a quote.

Usage: claude_session.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
AMBIENT_HOOK = REPO_ROOT / "hooks" / "ambient.py"

DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
RESET = "\033[0m"

PROMPT = "add retry backoff to the flaky sync test"
CALLS = [
    ("Read", {"file_path": "tests/test_sync.py"}, "Read 87 lines"),
    ("Grep", {"pattern": "retry", "path": "src/"}, "12 matches in 4 files"),
    ("Edit", {"file_path": "src/sync/backoff.py"}, "Updated src/sync/backoff.py with 9 additions, 2 removals"),
    ("Bash", {"command": "python3 -m pytest tests/test_sync.py -q"}, "14 passed in 2.1s"),
    ("Write", {"file_path": "docs/sync-notes.md"}, "Wrote 23 lines to docs/sync-notes.md"),
]


def type_out(text: str, delay: float = 0.035) -> None:
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write("\n")
    sys.stdout.flush()


def run_hook(tool: str, tool_input: dict) -> str | None:
    payload = {
        "session_id": "vhs-launch-demo",
        "hook_event_name": "PostToolUse",
        "tool_name": tool,
        "tool_input": tool_input,
    }
    proc = subprocess.run(
        [sys.executable, str(AMBIENT_HOOK), "--host", "claude"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=15,
    )
    try:
        return json.loads(proc.stdout or "{}").get("systemMessage")
    except json.JSONDecodeError:
        return None


def print_hook_message(tool: str, message: str) -> None:
    lines = message.splitlines() or [message]
    first, rest = lines[0], lines[1:]
    # First line carries the ~31-char "⎿ PostToolUse:<Tool> says:" prefix; keep the
    # whole rendered line inside the 127-col recording grid.
    wrapped = textwrap.wrap(first, width=88) or [first]
    sys.stdout.write(f"  ⎿  {CYAN}PostToolUse:{tool} says:{RESET} {wrapped[0]}\n")
    for cont in wrapped[1:]:
        sys.stdout.write(f"       {cont}\n")
    for line in rest:
        sys.stdout.write(f"       {line.strip()}\n")
    sys.stdout.flush()


def main() -> int:
    # Wipe the launch command off screen so the recording opens on a clean session.
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()
    time.sleep(0.8)
    sys.stdout.write(f"{DIM}>{RESET} ")
    sys.stdout.flush()
    type_out(PROMPT)
    time.sleep(1.0)

    for tool, tool_input, result in CALLS:
        arg = next(iter(tool_input.values()))
        sys.stdout.write(f"\n{BOLD}●{RESET} {tool}({arg})\n")
        sys.stdout.flush()
        time.sleep(0.55)
        sys.stdout.write(f"  ⎿  {DIM}{result}{RESET}\n")
        sys.stdout.flush()

        message = run_hook(tool, tool_input)
        if message:
            time.sleep(0.45)
            print_hook_message(tool, message)
            time.sleep(0.6)
        time.sleep(0.7)

    sys.stdout.write(f"\n{DIM}────────────────────────────────────────{RESET}\n")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
