"""Command-line interface for browsing, quotes, and ambient mode."""

from __future__ import annotations

import argparse
import json
import sys

from bookshelf import __version__


def _print_quote(*, as_json: bool, verbose: bool, tags: list[str], intent: str | None) -> int:
    from bookshelf.skill.quote_picker import (
        INTENT_TAGS,
        format_quote_details,
        format_quote_message,
        pick_quote,
        total_quote_count,
    )

    context_tags = list(tags)
    if intent:
        context_tags.extend(INTENT_TAGS[intent])
    from bookshelf.skill.quote_state import QuoteStateStore

    store = QuoteStateStore()
    if store.consume_recovery_notice():
        print(
            "Bookshelf recovered local companion state; the unreadable copy was quarantined.",
            file=sys.stderr,
        )
        return 1
    quote = pick_quote(context_tags or None)
    if not quote:
        if store.consume_recovery_notice():
            print(
                "Bookshelf recovered local companion state; the unreadable copy was quarantined.",
                file=sys.stderr,
            )
            return 1
        print("No quotes are available.", file=sys.stderr)
        return 1
    if as_json:
        print(json.dumps(quote, ensure_ascii=False))
    elif verbose:
        print(format_quote_details(quote, total_quote_count()))
    else:
        print(format_quote_message(quote, total_quote_count()))
    return 0


def _ambient_status(config: dict) -> None:
    enabled = bool(config.get("ambient_enabled", False))
    cadence = max(1, int(config.get("ambient_cadence", 5)))
    intent = str(config.get("ambient_intent", "neutral"))
    print(f"Ambient quotes: {'enabled' if enabled else 'disabled'}")
    print(f"Cadence: every {cadence} completed agent turn{'s' if cadence != 1 else ''}")
    print(f"Theme: {intent}")


def _ambient(action: str, cadence: int | None, intent: str | None) -> int:
    from bookshelf.storage import load_config, save_config

    config = load_config()
    if action == "enable":
        config["ambient_enabled"] = True
        if cadence is not None:
            config["ambient_cadence"] = cadence
        if intent is not None:
            config["ambient_intent"] = intent
        save_config(config)
    elif action == "disable":
        config["ambient_enabled"] = False
        save_config(config)
    _ambient_status(config)
    return 0


def _parser() -> argparse.ArgumentParser:
    from bookshelf.data.catalog import counts

    catalog_counts = counts()
    parser = argparse.ArgumentParser(
        prog="bookshelf",
        description=(
            f"Browse {catalog_counts['catalogued_books']:,} books or bring a "
            "contextual quote into your agent session."
        ),
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
    quote.add_argument("--verbose", action="store_true", help="include optional tags and counters")
    quote.add_argument(
        "--tag",
        action="append",
        default=[],
        help="prefer a context tag such as focus or resilience; repeatable",
    )
    quote.add_argument(
        "--intent",
        choices=("debug", "verify", "build", "ship", "review", "refactor", "collaborate", "recover", "neutral"),
        help="explicit, local intent hint; no terminal content is inspected",
    )

    feedback = commands.add_parser("feedback", help="vote on the last delivered quote")
    feedback.add_argument("vote", choices=("up", "down"))

    ambient = commands.add_parser("ambient", help="configure native agent companions")
    ambient.add_argument("action", choices=("enable", "disable", "status"))
    ambient.add_argument(
        "--cadence",
        type=int,
        help="emit after this many completed agent turns",
    )
    ambient.add_argument(
        "--intent",
        choices=(
            "debug",
            "verify",
            "build",
            "ship",
            "review",
            "refactor",
            "collaborate",
            "recover",
            "neutral",
        ),
        help="set a local quote theme without inspecting terminal content",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.command in (None, "browse"):
        from bookshelf.app import run

        run()
        return 0
    if args.command == "quote":
        return _print_quote(
            as_json=args.json,
            verbose=args.verbose,
            tags=args.tag,
            intent=args.intent,
        )
    if args.command == "feedback":
        from bookshelf.skill.quote_picker import set_last_quote_feedback

        if not set_last_quote_feedback(args.vote == "up"):
            print("No locally delivered quote is available for feedback.", file=sys.stderr)
            return 1
        print("Thanks — Bookshelf will use that local feedback for future picks.")
        return 0
    if args.command == "ambient":
        if args.cadence is not None and args.cadence < 1:
            _parser().error("--cadence must be >= 1")
        if args.intent is not None and args.action != "enable":
            _parser().error("--intent is only valid with ambient enable")
        return _ambient(args.action, args.cadence, args.intent)
    return 0
