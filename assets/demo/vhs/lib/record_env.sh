# Sourced by bookshelf-launch.tape (Hidden) to isolate recording state.
# Points HOME at a scratch dir so the ambient-state SQLite database and any
# bookshelf config are throwaway; real user state is never read or written.
#
# The staged session in lib/claude_session.py fires the hook once per tool
# call. Ambient delivery is opt-in and off by default, so this also writes a
# scratch config enabling it — the default cadence (5) then fires on the
# session's fifth and final call. No random seed is set: bookshelf's quote
# ranking is fully deterministic (relevance, then a stable ID tiebreak), so
# the same catalog and a fresh state directory always pick the same quote.
#
# Usage: source record_env.sh

export HOME="$(mktemp -d /tmp/vhs-home-XXXXXX)"

mkdir -p "$HOME/Library/Application Support/bookshelf"
printf '{"ambient_enabled": true}\n' > "$HOME/Library/Application Support/bookshelf/config.json"
