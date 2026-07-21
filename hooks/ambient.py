#!/usr/bin/env python3
"""Shared Codex, Claude Code, and Pi ambient adapter."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


def _detect_host() -> str:
    if os.environ.get("PLUGIN_ROOT"):
        return "codex"
    if os.environ.get("CLAUDE_PLUGIN_ROOT"):
        return "claude"
    return "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--host", default="auto")
    parser.add_argument("--plain", action="store_true")
    args, _ = parser.parse_known_args(argv)

    try:
        try:
            payload = json.load(sys.stdin)
        except (json.JSONDecodeError, OSError, TypeError):
            payload = {}

        host = _detect_host() if args.host == "auto" else args.host
        from bookshelf.ambient import ambient_message
        from bookshelf.skill.quote_picker import get_context_tags

        tags = get_context_tags(payload) if isinstance(payload, dict) else None
        message = ambient_message(host, context_tags=tags)
        if args.plain:
            if message:
                print(message)
        else:
            print(json.dumps({"systemMessage": message} if message else {}))
    except Exception:
        if not args.plain:
            print("{}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        raise SystemExit(0)
