# Catalog data

Bookshelf 1.0.0 contains 983 unique book records and 2,539 quote records across
fiction, science, motivation, philosophy, history, psychology, startup, and
romance.

## Provenance

The catalog was assembled and edited in the original Bookshelf project.
Bibliographic fields may be checked with the included Open Library helper, but
the current dataset does not retain a per-field source ledger. Summaries are
editorial descriptions stored with the project; they should not be represented
as publisher copy or authoritative literary criticism.

Quote records contain the text, attributed author, attributed book, optional
chapter text, and context tags. Many entries do not yet identify an edition,
page number, or primary-source scan. Attribution and punctuation can differ
between editions, and popular quotations are frequently misattributed.

The MIT license covers the software written for this repository. It does not
grant rights in third-party books or quoted text. Downstream distributors are
responsible for evaluating their use of the catalog.

## Corrections

Open an issue with:

- the current title, author, or quote text;
- the proposed correction;
- an authoritative source, preferably an edition, ISBN, chapter, and page;
- whether the correction affects duplicate records.

Corrections should preserve stable application state: do not rename a book
without checking favorites and reading-list migration behavior. Add or update a
focused regression test when a correction fixes a repeatable catalog problem.

## Refreshing counts

Counts in public documentation must come from the shipped modules:

```bash
python3 -c "from bookshelf.data.books import load_all_books; from bookshelf.data.quotes import QUOTES; print(len(load_all_books()), len(QUOTES))"
```
