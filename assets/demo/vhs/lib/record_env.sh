# Sourced by bookshelf-launch.tape (Hidden) to isolate recording state.
# BOOKSHELF_DATA_HOME confines the ambient-state SQLite database and config
# to a scratch temp directory — real user state is never read or written —
# and BOOKSHELF_AMBIENT_ENABLED opts the recording into ambient delivery
# without touching any config file.
#
# The staged session in lib/claude_session.py fires the hook once per tool
# call; the default cadence (5) then fires on the session's fifth and final
# call. No random seed is set: bookshelf's quote ranking is fully
# deterministic (relevance, then a stable ID tiebreak), so the same catalog
# and a fresh state directory always pick the same quote.
#
# Usage: source record_env.sh

export BOOKSHELF_DATA_HOME="$(mktemp -d /tmp/vhs-bookshelf-XXXXXX)"
export BOOKSHELF_AMBIENT_ENABLED=1
