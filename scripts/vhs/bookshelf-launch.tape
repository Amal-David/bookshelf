# Lightweight synthetic recording tool — NOT the production marketing demo.
# The README's hero clip (assets/demo/bookshelf-claude-demo.gif) is a real,
# captured Claude Code session with its own pagecast landing page; this tape
# is a fast, reproducible fallback for a quick terminal-only cut (e.g. for a
# changelog post or an issue repro), scripted with VHS: https://github.com/charmbracelet/vhs
#
# Run from the repo root: vhs scripts/vhs/bookshelf-launch.tape
# Beat 1: agent session with the ambient hook firing (real hook output)
# Beat 2: the bookshelf TUI (1,117 catalogued books, 8 genres)
# Beat 3: CTA

Require python3

Output scripts/vhs/output/bookshelf-launch.mp4
Output scripts/vhs/output/bookshelf-launch.gif

Set Theme "GruvboxDarkHard"
Set FontSize 20
Set Width 1560
Set Height 760
Set Padding 12
Set TypingSpeed 40ms
Set Framerate 30
Set WindowBar Colorful
Set WindowBarSize 36

# No random seed: bookshelf's quote ranking is fully deterministic (relevance,
# then a stable content-hash tiebreak), so a fresh scratch state directory
# always picks the same quote for this staged session. See lib/record_env.sh.

# --- setup (hidden): scratch HOME so no real state is touched ---
Hide
Type "source scripts/vhs/lib/record_env.sh && clear"
Enter
Type "python3 scripts/vhs/lib/claude_session.py"
Enter
Sleep 500ms
Show

# --- beat 1: session + hero quote ---
Wait+Screen@30s /PostToolUse/
Screenshot scripts/vhs/frames/bookshelf-hero.png
Sleep 4.5s
Wait@15s
Sleep 1s

# --- beat 2: the TUI ---
Hide
Type "clear"
Enter
Show
Type "python3 -m bookshelf"
Enter
Sleep 2.5s
Screenshot scripts/vhs/frames/bookshelf-shelf.png
Down@250ms 4
Sleep 800ms
Tab
Sleep 1s
Tab
Sleep 1s
Enter
Sleep 2s
Screenshot scripts/vhs/frames/bookshelf-detail.png
Right@500ms 2
Sleep 1.5s
Escape
Sleep 600ms
Escape
Sleep 1.5s

# --- beat 3: CTA ---
Hide
Enter
Sleep 300ms
Type "clear"
Enter
Sleep 300ms
Show
Type@60ms "# 1,117 books · 3,124 quotes · one hook — github.com/Amal-David/bookshelf"
Sleep 4s
Screenshot scripts/vhs/frames/bookshelf-cta.png
