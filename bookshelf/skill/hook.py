#!/usr/bin/env python3
"""Deprecated compatibility adapter for legacy Claude Code PostToolUse setup.

New installs use the bundled Claude plugin ``Stop`` hook.  This file remains
only for users who explicitly configured its old path; it now delegates to the
same opt-in, fail-closed ambient core as the bundled adapter.

Install by adding to ~/.claude/settings.json:
{
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/bookshelf/bookshelf/skill/hook.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = str(Path(__file__).resolve().parents[2])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Re-exported for backward compatibility (anything importing from hook.py keeps working).
from bookshelf.skill.quote_picker import (  # noqa: E402,F401
    RECENT_WINDOW,
    format_quote_message,
    get_context_tags,
    pick_quote,
    select_quote_index,
    total_quote_count,
)

HOOK_INPUT_MAX_BYTES = 16 * 1024


def read_hook_input() -> dict | None:
    """Read one bounded JSON event without retaining its raw bytes."""
    try:
        raw = sys.stdin.buffer.read(HOOK_INPUT_MAX_BYTES + 1)
    except (AttributeError, OSError):
        return None
    if len(raw) > HOOK_INPUT_MAX_BYTES:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def main():
    input_data = read_hook_input()
    if input_data is None:
        print(json.dumps({}))
        return

    try:
        from bookshelf.ambient import ambient_message

        message = ambient_message("claude", context_tags=get_context_tags(input_data))
        print(json.dumps({"systemMessage": message} if message else {}))
    except Exception:
        print(json.dumps({}))


if __name__ == "__main__":
    main()
