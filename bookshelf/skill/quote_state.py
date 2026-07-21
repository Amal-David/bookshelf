"""Concurrent-safe, private local state for ambient quote selection.

Only stable catalog identifiers, aggregate exposure, bounded recency, explicit
feedback, and host counters are retained.  Raw hook payloads never reach this
module.
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterable

from bookshelf.platform import app_data_dir

APP_DIR_NAME = "bookshelf"
DB_FILENAME = "ambient-state.sqlite3"
RECENT_LIMIT = 50
RECOVERY_NOTICE_FILENAME = "ambient-state-recovery.notice"
SQLITE_BUSY_TIMEOUT_MS = 10_000
SCHEMA_LOCK_RETRIES = 4


class StateRecoveryRequired(OSError):
    """State was quarantined; ambient delivery must remain silent until acknowledged."""


def state_db_path() -> Path:
    """Return the private, product-local SQLite database path."""
    directory = app_data_dir(APP_DIR_NAME)
    directory.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(directory, 0o700)
    except OSError:
        pass
    return directory / DB_FILENAME


def recovery_notice_path(path: Path | None = None) -> Path:
    """Return the one-shot interactive recovery marker for a state database."""
    database = Path(path) if path is not None else state_db_path()
    return database.parent / RECOVERY_NOTICE_FILENAME


class QuoteStateStore:
    """Small SQLite store with short transactions for competing hook processes."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path) if path is not None else state_db_path()
        self._initialized = False

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError:
            pass
        connection = sqlite3.connect(
            self.path,
            timeout=SQLITE_BUSY_TIMEOUT_MS / 1000,
            isolation_level=None,
        )
        try:
            connection.row_factory = sqlite3.Row
            connection.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
            connection.execute("PRAGMA synchronous = NORMAL")
            self._secure_state_paths()
        except BaseException:
            connection.close()
            raise
        return connection

    def _secure_state_paths(self) -> None:
        """SQLite may create sidecars; keep every local state artifact private."""
        for path in (
            self.path,
            self.path.with_name(f"{self.path.name}-journal"),
            self.path.with_name(f"{self.path.name}-wal"),
            self.path.with_name(f"{self.path.name}-shm"),
        ):
            try:
                if path.exists():
                    os.chmod(path, 0o600)
            except OSError:
                pass

    @contextmanager
    def _managed_connection(self):
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()

    def _ensure_schema(self) -> None:
        if self._initialized:
            return
        for attempt in range(SCHEMA_LOCK_RETRIES):
            try:
                self._create_schema()
                self._initialized = True
                return
            except sqlite3.OperationalError as error:
                # A competing first-run process is not corruption. Let SQLite's
                # busy timeout work, then retry without moving live state files.
                if "locked" not in str(error).casefold() or attempt + 1 == SCHEMA_LOCK_RETRIES:
                    raise
                time.sleep(0.025 * (attempt + 1))
            except sqlite3.DatabaseError:
                # A corrupt local cache must not break an agent turn. Preserve
                # it for inspection and make one clean replacement next time.
                self._quarantine_state_files()
                self._initialized = False
                self._create_schema()
                self._write_recovery_notice()
                raise StateRecoveryRequired("Bookshelf companion state was quarantined")

    @staticmethod
    def _quarantine_file(path: Path) -> None:
        corrupt = path.with_name(f"{path.name}.corrupt-{int(time.time())}-{os.getpid()}")
        try:
            path.replace(corrupt)
        except OSError:
            pass

    def _quarantine_state_files(self) -> None:
        """Quarantine the database together with any SQLite sidecars."""
        for candidate in (
            self.path,
            self.path.with_name(f"{self.path.name}-journal"),
            self.path.with_name(f"{self.path.name}-wal"),
            self.path.with_name(f"{self.path.name}-shm"),
        ):
            self._quarantine_file(candidate)

    def _create_schema(self) -> None:
        with self._managed_connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS exposure (quote_id TEXT PRIMARY KEY, shown_count INTEGER NOT NULL DEFAULT 0, last_seen_ms INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS recent_quote (sequence INTEGER PRIMARY KEY AUTOINCREMENT, quote_id TEXT NOT NULL, shown_at_ms INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS recent_quote_id_idx ON recent_quote (quote_id);
                CREATE TABLE IF NOT EXISTS feedback (quote_id TEXT PRIMARY KEY, value INTEGER NOT NULL CHECK (value IN (-1, 1)), updated_at_ms INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS counter (key TEXT PRIMARY KEY, value INTEGER NOT NULL DEFAULT 0);
                """
            )
            expected = {
                "metadata": {"key", "value"},
                "exposure": {"quote_id", "shown_count", "last_seen_ms"},
                "recent_quote": {"sequence", "quote_id", "shown_at_ms"},
                "feedback": {"quote_id", "value", "updated_at_ms"},
                "counter": {"key", "value"},
            }
            for table, columns in expected.items():
                found = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
                if not columns.issubset(found):
                    raise sqlite3.DatabaseError(f"unknown {table} schema")
            # WAL persists once enabled. During a simultaneous first run, the
            # schema is already usable with SQLite's rollback journal, so a
            # transient lock here must not be treated as corruption or failure.
            journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
            if str(journal_mode).casefold() != "wal":
                try:
                    connection.execute("PRAGMA journal_mode = WAL")
                except sqlite3.OperationalError as error:
                    if "locked" not in str(error).casefold():
                        raise
        self._secure_state_paths()

    def _write_recovery_notice(self) -> None:
        marker = recovery_notice_path(self.path)
        try:
            descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            return
        except OSError:
            return
        os.close(descriptor)

    def recovery_notice_pending(self) -> bool:
        return recovery_notice_path(self.path).is_file()

    def consume_recovery_notice(self) -> bool:
        marker = recovery_notice_path(self.path)
        try:
            marker.unlink()
            return True
        except FileNotFoundError:
            return False
        except OSError:
            return False

    def migrate_legacy_indices(self, quote_ids: Iterable[str], legacy_path: Path) -> None:
        """Map old positional JSON history to stable IDs once, preserving valid rows."""
        self._ensure_schema()
        with self._managed_connection() as connection:
            done = connection.execute(
                "SELECT 1 FROM metadata WHERE key = 'legacy-index-migration-v1'"
            ).fetchone()
        if done:
            return
        ids = list(quote_ids)
        try:
            payload = json.loads(legacy_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            payload = {}
        except (OSError, ValueError, TypeError):
            self._quarantine_file(legacy_path)
            self._write_recovery_notice()
            raise StateRecoveryRequired("Bookshelf legacy companion state was quarantined")
        if not isinstance(payload, dict):
            self._quarantine_file(legacy_path)
            self._write_recovery_notice()
            raise StateRecoveryRequired("Bookshelf legacy companion state was quarantined")
        shown_counts = payload.get("shown_counts", {})
        recent_indices = payload.get("recent_indices", [])
        if not isinstance(shown_counts, dict):
            shown_counts = {}
        if not isinstance(recent_indices, list):
            recent_indices = []
        now = int(time.time() * 1000)
        with self._managed_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            done = connection.execute(
                "SELECT 1 FROM metadata WHERE key = 'legacy-index-migration-v1'"
            ).fetchone()
            if done:
                connection.commit()
                return
            for raw_index, raw_count in shown_counts.items():
                try:
                    quote_id = ids[int(raw_index)]
                    count = max(0, int(raw_count))
                except (ValueError, TypeError, IndexError):
                    continue
                if count:
                    connection.execute(
                        "INSERT INTO exposure(quote_id, shown_count, last_seen_ms) VALUES (?, ?, ?) "
                        "ON CONFLICT(quote_id) DO UPDATE SET shown_count = MAX(exposure.shown_count, excluded.shown_count)",
                        (quote_id, count, now),
                    )
            for position, raw_index in enumerate(recent_indices[-RECENT_LIMIT:]):
                try:
                    quote_id = ids[int(raw_index)]
                except (ValueError, TypeError, IndexError):
                    continue
                connection.execute(
                    "INSERT INTO recent_quote(quote_id, shown_at_ms) VALUES (?, ?)",
                    (quote_id, now + position),
                )
            connection.execute(
                "INSERT INTO metadata(key, value) VALUES ('legacy-index-migration-v1', 'complete')"
            )
            connection.commit()

    def snapshot(self) -> tuple[dict[str, int], list[str], dict[str, int]]:
        """Return only the bounded ranking state needed for a selection."""
        self._ensure_schema()
        with self._managed_connection() as connection:
            return self._snapshot_from_connection(connection)

    @staticmethod
    def _snapshot_from_connection(
        connection: sqlite3.Connection,
    ) -> tuple[dict[str, int], list[str], dict[str, int]]:
        counts = {
            row["quote_id"]: int(row["shown_count"])
            for row in connection.execute("SELECT quote_id, shown_count FROM exposure")
        }
        recent = [
            row["quote_id"]
            for row in connection.execute(
                "SELECT quote_id FROM recent_quote ORDER BY sequence DESC LIMIT ?",
                (RECENT_LIMIT,),
            )
        ]
        feedback = {
            row["quote_id"]: int(row["value"])
            for row in connection.execute("SELECT quote_id, value FROM feedback")
        }
        return counts, recent, feedback

    @staticmethod
    def _record_on_connection(
        connection: sqlite3.Connection, quote_id: str, now: int
    ) -> tuple[int, int]:
        connection.execute(
            "INSERT INTO exposure(quote_id, shown_count, last_seen_ms) VALUES (?, 1, ?) "
            "ON CONFLICT(quote_id) DO UPDATE SET shown_count = shown_count + 1, last_seen_ms = excluded.last_seen_ms",
            (quote_id, now),
        )
        connection.execute(
            "INSERT INTO recent_quote(quote_id, shown_at_ms) VALUES (?, ?)",
            (quote_id, now),
        )
        connection.execute(
            "INSERT INTO metadata(key, value) VALUES ('last-quote-id', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (quote_id,),
        )
        connection.execute(
            "DELETE FROM recent_quote WHERE sequence NOT IN "
            "(SELECT sequence FROM recent_quote ORDER BY sequence DESC LIMIT ?)",
            (RECENT_LIMIT,),
        )
        row = connection.execute(
            "SELECT shown_count FROM exposure WHERE quote_id = ?", (quote_id,)
        ).fetchone()
        unique = connection.execute("SELECT COUNT(*) FROM exposure").fetchone()[0]
        return int(row[0]), int(unique)

    def select_and_record(
        self,
        selector: Callable[[dict[str, int], list[str], dict[str, int]], str],
    ) -> tuple[str, int, int]:
        """Serialize snapshot, deterministic selection, and exposure recording."""
        self._ensure_schema()
        with self._managed_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                counts, recent, feedback = self._snapshot_from_connection(connection)
                quote_id = selector(counts, recent, feedback)
                if not isinstance(quote_id, str) or not quote_id:
                    raise ValueError("selector returned an invalid quote ID")
                shown, unique = self._record_on_connection(
                    connection, quote_id, int(time.time() * 1000)
                )
                connection.commit()
            except BaseException:
                connection.rollback()
                raise
        return quote_id, shown, unique

    def record_selection(self, quote_id: str) -> tuple[int, int]:
        """Atomically record a quote exposure and keep bounded recency."""
        self._ensure_schema()
        now = int(time.time() * 1000)
        with self._managed_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            shown, unique = self._record_on_connection(connection, quote_id, now)
            connection.commit()
        return shown, unique

    def last_quote_id(self) -> str | None:
        self._ensure_schema()
        with self._managed_connection() as connection:
            row = connection.execute(
                "SELECT value FROM metadata WHERE key = 'last-quote-id'"
            ).fetchone()
        return str(row[0]) if row else None

    def increment_counter(self, key: str) -> int:
        """Increment a host cadence counter without a JSON read/modify/write race."""
        self._ensure_schema()
        with self._managed_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                "INSERT INTO counter(key, value) VALUES (?, 1) "
                "ON CONFLICT(key) DO UPDATE SET value = value + 1",
                (key,),
            )
            value = connection.execute("SELECT value FROM counter WHERE key = ?", (key,)).fetchone()[0]
            connection.commit()
        return int(value)

    def set_feedback(self, quote_id: str, helpful: bool) -> None:
        self._ensure_schema()
        with self._managed_connection() as connection:
            connection.execute(
                "INSERT INTO feedback(quote_id, value, updated_at_ms) VALUES (?, ?, ?) "
                "ON CONFLICT(quote_id) DO UPDATE SET value = excluded.value, updated_at_ms = excluded.updated_at_ms",
                (quote_id, 1 if helpful else -1, int(time.time() * 1000)),
            )
