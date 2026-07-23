# Recording a quick terminal demo

The README's hero clip (`assets/demo/bookshelf-claude-demo.gif`) is a real,
captured Claude Code session with its own accessible, narrated landing page
at [site/](../../site/) — that is the production marketing asset and this
tooling does not replace it.

This directory is a lightweight, reproducible way to record a synthetic
terminal-only cut with [VHS](https://github.com/charmbracelet/vhs) (e.g. for
a changelog post, a bug repro, or a quick preview while iterating on the TUI).

## Usage

```bash
brew install vhs   # or see the VHS install docs
vhs scripts/vhs/bookshelf-launch.tape
```

Outputs land in `scripts/vhs/output/` (gitignored) and per-beat screenshots
in `scripts/vhs/frames/`. Neither is committed — re-run the tape to regenerate.

## How it works

- `lib/record_env.sh` points `$HOME` at a scratch temp directory so the
  ambient-state SQLite database and config are throwaway; your real bookshelf
  state is never read or written. It also opts the scratch config into
  ambient delivery (`ambient_enabled: true`) so the staged session's fifth
  tool call — the default cadence — surfaces a quote.
- `lib/claude_session.py` prints a staged Claude Code-style transcript at
  reading pace while piping real event JSON into the actual shared hook
  (`hooks/ambient.py`). The quote on screen is genuine hook output; only the
  session pacing and the surrounding tool-call narration are staged.
- No random seed is needed or set. Bookshelf's quote ranking
  (`bookshelf/skill/quote_picker.py:select_quote_index`) is fully
  deterministic — relevance first, then a stable content-hash tiebreak — so a
  fresh scratch state directory always selects the same quote for this
  five-call session.
