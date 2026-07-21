"""Command-line interface for browsing, quotes, and ambient mode."""

from __future__ import annotations

import argparse
import json
import sys

from bookshelf import __version__


def _print_quote(*, as_json: bool, tags: list[str]) -> int:
    from bookshelf.skill.quote_picker import (
        format_quote_message,
        pick_quote,
        total_quote_count,
    )

    quote = pick_quote(tags or None)
    if not quote:
        print("No quotes are available.", file=sys.stderr)
        return 1
    if as_json:
        print(json.dumps(quote, ensure_ascii=False))
    else:
        print(format_quote_message(quote, total_quote_count()))
    return 0


def _ambient_status(config: dict) -> None:
    enabled = bool(config.get("ambient_enabled", False))
    cadence = max(1, int(config.get("ambient_cadence", 5)))
    print(f"Ambient quotes: {'enabled' if enabled else 'disabled'}")
    print(f"Cadence: every {cadence} completed agent turn{'s' if cadence != 1 else ''}")


def _ambient(action: str, cadence: int | None) -> int:
    from bookshelf.storage import load_config, save_config

    config = load_config()
    if action == "enable":
        config["ambient_enabled"] = True
        if cadence is not None:
            config["ambient_cadence"] = cadence
        save_config(config)
    elif action == "disable":
        config["ambient_enabled"] = False
        save_config(config)
    _ambient_status(config)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bookshelf",
        description="Browse 983 books or bring a contextual quote into your agent session.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    commands = parser.add_subparsers(dest="command")

    commands.add_parser("browse", help="open the interactive terminal bookshelf")

    quote = commands.add_parser("quote", help="show one quote on demand")
    quote.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    quote.add_argument(
        "--tag",
        action="append",
        default=[],
        help="prefer a context tag such as focus or resilience; repeatable",
    )

    ambient = commands.add_parser("ambient", help="configure native agent companions")
    ambient.add_argument("action", choices=("enable", "disable", "status"))
    ambient.add_argument(
        "--cadence",
        type=int,
        help="emit after this many completed agent turns",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command in (None, "browse"):
        from bookshelf.app import run

        run()
        return 0
    if args.command == "quote":
        return _print_quote(as_json=args.json, tags=args.tag)
    if args.command == "ambient":
        if args.cadence is not None and args.cadence < 1:
            _parser().error("--cadence must be >= 1")
        return _ambient(args.action, args.cadence)
    return 0
