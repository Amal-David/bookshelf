"""Generated v2 primary-source catalog loader.

The JSON is data-only so quote selection stays deterministic and has no network
or model dependency. It is written by ``scripts/compile_catalog.py``.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


_CATALOG_PATH = Path(__file__).with_name("catalog_v2.json")


@lru_cache(maxsize=1)
def load_catalog_v2() -> dict[str, Any]:
    return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def load_v2_quotes() -> list[dict[str, Any]]:
    return list(load_catalog_v2()["quotes"])


def load_v2_books() -> list[dict[str, Any]]:
    return list(load_catalog_v2()["books"])
