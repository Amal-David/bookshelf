---
name: bookshelf
description: Select a verified entry from Bookshelf's curated quote catalog and present it with its author, book, and context tags. Use when a user asks for a book quote, a literary companion for the current task or mood, motivation from a book, or help configuring Bookshelf's optional ambient quote mode.
---

# Use Bookshelf

Resolve `<skill-dir>` to the directory containing this `SKILL.md`, then run:

```bash
python3 "<skill-dir>/scripts/quote.py" --json
```

Add one or more `--tag` values when the user's context is clear:

```bash
python3 "<skill-dir>/scripts/quote.py" --json --tag focus --tag resilience
```

Use the returned text, author, and book exactly as provided. Do not invent an
edition, chapter, page number, or provenance that is absent from the result.
Keep the response compact unless the user asks for interpretation.

For ambient mode, explain that it is opt-in and ask before changing it. When the
user explicitly approves, use:

```bash
bookshelf ambient enable --cadence 5
```

Use `bookshelf ambient status` to inspect it and `bookshelf ambient disable` to
turn it off. In Codex desktop and Claude Code, ambient quotes appear as
lifecycle event banners. They are not appended to assistant response text. Pi
uses a native companion entry; Hermes may append the quote to the completed
response.

Never enable ambient mode implicitly, edit an agent's global configuration
without permission, or treat a failed adapter as a reason to fail the user's
main task.
