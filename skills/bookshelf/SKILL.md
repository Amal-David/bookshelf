---
name: bookshelf
description: Select a compact Bookshelf quote and present it with its author, book, and context tags. Do not represent every catalog record as verified or curated. Use when a user asks for a book quote, a literary companion for the current task or mood, motivation from a book, or help configuring Bookshelf's optional ambient quote mode.
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

For an explicit on-demand work intent, prefer the local CLI boundary:

```bash
bookshelf quote --intent refactor
bookshelf feedback up|down
```

Use the returned text, author, and book exactly as provided. Do not invent an
edition, chapter, page number, or provenance that is absent from the result.
Keep the response compact unless the user asks for interpretation.
Intent matching uses an explicit intent or bounded host metadata label only; it
does not inspect commands, paths, prompts, transcripts, code, tool arguments,
model output, or network calls. Ambient mode is optional, off by default, and
fails closed when a safe bounded signal is unavailable.

For ambient mode, explain that it is opt-in and ask before changing it. When the
user explicitly approves, use:

```bash
bookshelf ambient enable --cadence 5 --intent refactor
```

Use `bookshelf ambient status` to inspect it and `bookshelf ambient disable` to
turn it off. Host adapters are optional and host-specific. Their install,
manifest, loader, and adapter contracts are tested in isolation; do not
describe a banner, notification, appended output, authenticated turn, or Codex
Desktop behavior as observed unless it has been verified in that host.

Never enable ambient mode implicitly, edit an agent's global configuration
without permission, or treat a failed adapter as a reason to fail the user's
main task.
