"""Platform-aware paths and atomic persistence helpers."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any


def app_data_dir(app_dir_name: str, base_dir: Path | None = None) -> Path:
    """Return the app data directory while preserving test overrides.

    ``BOOKSHELF_DATA_HOME`` names the bookshelf data directory itself and
    redirects the whole local state surface (config, legacy hook state, and
    the ambient SQLite store). An explicit ``base_dir`` argument still wins;
    a blank value means unset because the sandboxed hook wrappers always
    export the variable, possibly empty.
    """
    if base_dir is not None:
        return Path(base_dir)

    override = os.environ.get("BOOKSHELF_DATA_HOME", "").strip()
    if override:
        return Path(override).expanduser()

    home = Path.home()
    if sys.platform == "darwin":
        root = home / "Library" / "Application Support"
    elif os.name == "nt":
        root = Path(os.environ.get("APPDATA", home / "AppData" / "Roaming"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
    return root / app_dir_name


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8") -> None:
    """Atomically replace *path* with *text* on the same filesystem."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding=encoding) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def atomic_write_json(
    path: Path,
    payload: Any,
    *,
    indent: int | None = 2,
    ensure_ascii: bool = False,
) -> None:
    """Serialize JSON and atomically replace the target file."""
    atomic_write_text(
        path,
        json.dumps(payload, indent=indent, ensure_ascii=ensure_ascii),
    )
