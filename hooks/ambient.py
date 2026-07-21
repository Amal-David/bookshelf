#!/usr/bin/env python3
"""Shared Codex, Claude Code, and Pi ambient adapter."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
HOOK_INPUT_MAX_BYTES = 16 * 1024
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


def _detect_host() -> str:
    if os.environ.get("PLUGIN_ROOT"):
        return "codex"
    if os.environ.get("CLAUDE_PLUGIN_ROOT"):
        return "claude"
    return "unknown"


def _read_payload() -> dict | None:
    """Bound hook input before parsing; never retain raw event content."""
    try:
        buffer = getattr(sys.stdin, "buffer", None)
        raw = (
            buffer.read(HOOK_INPUT_MAX_BYTES + 1)
            if buffer is not None
            else sys.stdin.read(HOOK_INPUT_MAX_BYTES + 1).encode("utf-8")
        )
    except (AttributeError, OSError, UnicodeEncodeError):
        return None
    if len(raw) > HOOK_INPUT_MAX_BYTES:
        return None
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--host", default="auto")
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--no-event", action="store_true")
    args, _ = parser.parse_known_args(argv)

    try:
        # Pi's native end-of-turn callback intentionally has no event body.
        # This explicit switch is not a fallback for malformed hook input.
        payload = {} if args.no_event else _read_payload()
        if payload is None:
            if not args.plain:
                print("{}")
            return 0

        host = _detect_host() if args.host == "auto" else args.host
        from bookshelf.ambient import ambient_message
        from bookshelf.skill.quote_picker import get_context_tags

        tags = get_context_tags(payload)
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
