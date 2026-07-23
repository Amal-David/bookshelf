# VHS launch video

`bookshelf-launch.mp4` and `bookshelf-launch.gif` in this directory are a
synthetic, VHS-scripted terminal recording: a staged agent session firing the
real ambient hook, then a tour of the terminal library, then a CTA card.

This is **not** the README's hero clip. `assets/demo/bookshelf-claude-demo.gif`
one level up is a real, captured Claude Code 2.1.217 + Opus 4.8 session with
its own accessible pagecast landing page (transcript, poster image, video) —
that's the production marketing asset, hand-refined across several commits,
and this directory does not replace or reference it. Both currently ship in
the repo; swapping the README's top-of-page hero to this VHS video instead
(or showing both) is a one-line edit to `README.md` line 5 whenever you want
to make that call.

## Regenerating the video

```bash
brew install vhs   # or see https://github.com/charmbracelet/vhs
vhs assets/demo/vhs/bookshelf-launch.tape
```

Re-running the tape regenerates `bookshelf-launch.mp4`/`.gif` in place — they
are both the source recipe and the tracked output. Per-beat screenshots land
in `assets/demo/vhs/frames/` (gitignored; not part of the deliverable).

## How it works

- `lib/record_env.sh` points `$HOME` at a scratch temp directory so the
  ambient-state SQLite database and config are throwaway; your real bookshelf
  state is never read or written. It also opts the scratch config into
  ambient delivery (`ambient_enabled: true`) so the staged session's fifth
  tool call — the default cadence — surfaces a quote.
- `lib/claude_session.py` prints a staged Claude Code-style transcript at
  reading pace while piping real event JSON into the actual shared hook
  (`hooks/ambient.py`, invoked with `--host claude`). The quote on screen is
  genuine hook output; only the session pacing and the surrounding tool-call
  narration are staged.
- No random seed is needed or set. Bookshelf's quote ranking
  (`bookshelf/skill/quote_picker.py:select_quote_index`) is fully
  deterministic — relevance first, then a stable content-hash tiebreak — so a
  fresh scratch state directory always selects the same quote for this
  five-call session. Verified with repeated dry runs before this was
  committed: identical quote every time.
