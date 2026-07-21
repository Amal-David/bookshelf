# Catalog data

Bookshelf's shipped totals are generated, rather than copied into this page.
See [`docs/catalog-counts.md`](docs/catalog-counts.md) and
[`bookshelf/data/catalog_manifest.json`](bookshelf/data/catalog_manifest.json)
for the current catalogued-book, quoted-work, source, rights, verification, and
rejection counts.

The current generated totals are 3,124 quote records, 3,111 normalized unique
texts, 1,117 catalogued books, and 949 works referenced by quotes. Of those
records, 585 v2 records are primary-source-linked but remain pending human
review; 2,539 legacy records are explicitly `legacy-unverified`. These totals
must not be used to claim that every quote is verified or editorially curated.

## Provenance

The catalog was assembled and edited in the original Bookshelf project.
Bibliographic fields may be checked with the included Open Library helper, but
the current dataset does not retain a per-field source ledger. Summaries are
editorial descriptions stored with the project; they should not be represented
as publisher copy or authoritative literary criticism.

Legacy quote records contain the text, attributed author, attributed book,
optional chapter text, and context tags. They are deliberately labeled
`legacy-unverified`: many do not identify an edition, page number, or
primary-source scan, and attribution and punctuation can differ between
editions.

The v2 import contains only records linked to a Standard Ebooks source bundle.
Each has a stable quote and work ID, normalized-text digest, source identifier
and repository URL, XHTML locator, extraction-snapshot digest, rights class,
U.S. jurisdiction note, verification date/state, and explicit
`review-pending-human-review` admission status. The compiler checks those IDs,
digests, locator fields, URL shapes, and safety gates. The original staging
fetches used moving repository branches rather than immutable commit pins, so
the records are deliberately labeled `source-linked-review-pending`; this is
not a machine or human verification claim. The source edition is CC0-dedicated
and the underlying texts are marked public domain in the United States; this is
not a worldwide clearance claim.
Opaque quote aggregators and records with missing provenance, unresolved works,
unsupported rights, control characters, unsafe lengths, exact duplicates, or
near duplicates are rejected by the offline compiler.

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

Counts in public documentation must come from the generated manifest:

```bash
python3 scripts/compile_catalog.py --check
python3 -c "from bookshelf.data.catalog import counts; print(counts())"
```
