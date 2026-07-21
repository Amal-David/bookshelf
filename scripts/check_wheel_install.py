#!/usr/bin/env python3
"""Install a built wheel into a clean venv and smoke-test its public CLI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_wheel_install.py PATH_TO_WHEEL", file=sys.stderr)
        return 2

    wheel = Path(sys.argv[1]).resolve()
    if not wheel.is_file():
        print(f"wheel not found: {wheel}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        environment = root / "venv"
        venv.EnvBuilder(with_pip=True).create(environment)
        if sys.platform == "win32":
            python = environment / "Scripts" / "python.exe"
            bookshelf = environment / "Scripts" / "bookshelf.exe"
        else:
            python = environment / "bin" / "python"
            bookshelf = environment / "bin" / "bookshelf"

        home = root / "home"
        home.mkdir()
        clean_env = dict(os.environ)
        clean_env["HOME"] = str(home)
        clean_env["APPDATA"] = str(home / "AppData" / "Roaming")

        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                str(wheel),
            ],
            check=True,
            env=clean_env,
        )
        version = subprocess.run(
            [str(bookshelf), "--version"],
            check=True,
            capture_output=True,
            text=True,
            env=clean_env,
        ).stdout.strip()
        quote = subprocess.run(
            [str(bookshelf), "quote", "--json"],
            check=True,
            capture_output=True,
            text=True,
            env=clean_env,
        ).stdout
        payload = json.loads(quote)
        if version != "bookshelf 1.0.0":
            raise SystemExit(f"unexpected version: {version}")
        if not {"text", "author", "book"} <= payload.keys():
            raise SystemExit("quote response is missing required fields")
    print("isolated wheel install: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
