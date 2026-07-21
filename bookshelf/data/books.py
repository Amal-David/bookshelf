"""Unified book catalog — imports from genre-specific modules."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Book:
    title: str
    author: str
    year: int
    genre: str
    mood: list[str]
    summary: str
    ol_key: str = ""
    work_id: str = ""
    source_identifier: str = ""
    source_url: str = ""
    rights_class: str = "legacy-unknown"
    rights_jurisdiction_note: str = ""
    verification_state: str = "legacy-unverified"
    verified_at: str = ""
    digest_sha256: str = ""
    summary_kind: str = "editorial"

    @property
    def spine_label(self) -> str:
        """Short label for shelf spine display."""
        max_title = 20
        t = self.title if len(self.title) <= max_title else self.title[: max_title - 1] + "…"
        return t


def _dicts_to_books(dicts: list[dict]) -> list[Book]:
    """Convert raw dicts from genre modules into Book objects."""
    books = []
    for d in dicts:
        books.append(
            Book(
                title=d["title"],
                author=d["author"],
                year=d["year"],
                genre=d["genre"],
                mood=d.get("mood", []),
                summary=d.get("summary", ""),
                ol_key=d.get("ol_key", ""),
                work_id=d.get("work_id", ""),
                source_identifier=d.get("source_identifier", ""),
                source_url=d.get("source_url", ""),
                rights_class=d.get("rights_class", "legacy-unknown"),
                rights_jurisdiction_note=d.get("rights_jurisdiction_note", ""),
                verification_state=d.get("verification_state", "legacy-unverified"),
                verified_at=d.get("verified_at", ""),
                digest_sha256=d.get("digest_sha256", ""),
                summary_kind=d.get("summary_kind", "editorial"),
            )
        )
    return books


def load_all_books() -> list[Book]:
    """Load and merge all books from genre catalogs."""
    from bookshelf.data.books_motivation import MOTIVATION_BOOKS
    from bookshelf.data.books_startup import STARTUP_BOOKS
    from bookshelf.data.books_romance import ROMANCE_BOOKS
    from bookshelf.data.books_fiction import FICTION_BOOKS
    from bookshelf.data.books_science import SCIENCE_BOOKS
    from bookshelf.data.books_philosophy import PHILOSOPHY_BOOKS
    from bookshelf.data.books_psychology import PSYCHOLOGY_BOOKS
    from bookshelf.data.books_history import HISTORY_BOOKS
    from bookshelf.data.catalog_v2 import load_v2_books

    all_books = []
    # A title is not a bibliographic identity: v2 includes different authors'
    # distinct works with the same title.
    seen_works: set[tuple[str, str]] = set()

    for dicts in (
        MOTIVATION_BOOKS,
        STARTUP_BOOKS,
        ROMANCE_BOOKS,
        FICTION_BOOKS,
        SCIENCE_BOOKS,
        PHILOSOPHY_BOOKS,
        PSYCHOLOGY_BOOKS,
        HISTORY_BOOKS,
        load_v2_books(),
    ):
        for book in _dicts_to_books(dicts):
            identity = (book.title.casefold(), book.author.casefold())
            if identity not in seen_works:
                all_books.append(book)
                seen_works.add(identity)

    all_books.sort(key=lambda b: (b.genre, b.title.lower()))
    return all_books


def filter_books(
    books: list[Book], genre: str | None = None, query: str | None = None
) -> list[Book]:
    """Filter books by genre and/or search query."""
    result = books
    if genre and genre != "all":
        result = [b for b in result if b.genre == genre]
    if query:
        q = query.lower()
        result = [
            b
            for b in result
            if q in b.title.lower() or q in b.author.lower()
        ]
    return result
