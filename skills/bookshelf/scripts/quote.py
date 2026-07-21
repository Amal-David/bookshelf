#!/usr/bin/env python3
"""Portable skill wrapper for Bookshelf's deterministic quote command."""

from __future__ import annotations

import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from bookshelf.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["quote", *sys.argv[1:]]))
