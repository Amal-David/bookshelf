# Bookshelf

Bookshelf is a terminal library of **983 books** and **2,539 quotes**. Browse
books, keep reading lists, ask your coding agent for a fitting quote, or opt in
to a quiet literary companion while you work.

![Bookshelf browse view](assets/screenshots/bookshelf_browse.png)

## Two ways to use it

**On demand** is the default. Invoke the Bookshelf skill or run:

```bash
bookshelf quote
bookshelf quote --tag focus --json
```

**Ambient mode** is optional:

```bash
bookshelf ambient enable --cadence 5
bookshelf ambient status
bookshelf ambient disable
```

Installing an agent integration does not enable ambient mode. Adapters swallow
their own failures so a quote can never break the agent's actual turn.

## Install

Bookshelf requires Python 3.10 or newer and has no runtime dependencies.

```bash
pipx install git+https://github.com/Amal-David/bookshelf.git
# After the first PyPI release:
# pipx install ambient-bookshelf
```

Then run `bookshelf` to open the interactive library.

### Codex desktop and CLI

```bash
codex plugin marketplace add Amal-David/bookshelf
codex plugin add bookshelf@bookshelf
```

Restart the desktop app, open **Plugins**, choose the **Bookshelf** marketplace,
and install Bookshelf. The skill is available on demand. If ambient mode is
enabled, the bundled `Stop` hook surfaces a lifecycle event banner; it does not
rewrite assistant response text. Codex asks you to review and trust the hook
before it runs.

### Claude Code

Run these inside Claude Code:

```text
/plugin marketplace add Amal-David/bookshelf
/plugin install bookshelf@bookshelf
```

The on-demand skill works independently of ambient mode. Ambient quotes use the
shared `Stop` hook and appear as system event output rather than authored
assistant text.

### Pi

```bash
pi install git:github.com/Amal-David/bookshelf
```

Pi loads the canonical skill and a small `agent_end` extension. When ambient
mode is enabled, the extension renders the due quote as a native companion
notification without sending it back to the model.

### Hermes

```bash
hermes plugins install Amal-David/bookshelf --enable
```

Hermes registers the canonical skill plus a `transform_llm_output` hook. When
ambient mode is enabled and its cadence is due, Hermes appends the quote after
the completed response. The hook uses no additional model call.

These manifests follow the current host contracts, but the initial release
still needs hands-on installation checks in each host before those surfaces are
called fully validated.

## Library

| Genre | Books |
|---|---:|
| Fiction | 176 |
| Science | 151 |
| Motivation | 132 |
| Philosophy | 132 |
| History | 116 |
| Psychology | 97 |
| Startup | 96 |
| Romance | 83 |
| **Total** | **983** |

Each book has an editorial summary, mood tags, and bibliographic metadata.
Quotes carry context tags used to prefer relevant entries for work such as
debugging, building, reviewing, or shipping. See [DATA.md](DATA.md) for
provenance and the correction policy.

## Terminal library

```bash
bookshelf
```

![Book detail view](assets/screenshots/bookshelf_detail.png)

| Key | Action |
|---|---|
| `Up` / `Down` / `j` / `k` | Navigate |
| `Enter` / `Right` | Open a book |
| `Tab` / `Shift+Tab` | Cycle genres |
| `/` | Search |
| `c` | Open reading lists |
| `r` | Pick a random book |
| `f` | Toggle favorite |
| `m` | Mark as read |
| `w` | Add to want-to-read |
| `?` | Show help |
| `q` | Go back or quit |

Favorites, reading lists, statistics, hook counters, and ambient settings remain
local under the platform application-data directory named `bookshelf`.

## Demo video

![Ambient quote example](assets/screenshots/bookshelf_ambient_hook.png)

[Watch the 20-second Bookshelf demo](site/public/bookshelf-demo.mp4).

The landing-page source lives in [`site/`](site/). It is built from the same
forest, paper, and rose visual system as the demo.

## Development

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q bookshelf hooks scripts tests
python3 -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for catalog corrections and code
contributions.

## License

The application code is MIT licensed. Book titles, author names, summaries, and
quoted text have separate provenance and rights considerations described in
[DATA.md](DATA.md).
