"""Color pair definitions for the bookshelf TUI."""

import curses

# Color pair IDs
SHELF_FRAME = 1
TITLE_HIGHLIGHT = 2
BODY_TEXT = 3
GENRE_MOTIVATION = 4
GENRE_ROMANCE = 5
GENRE_STARTUP = 6
FAVORITE_HEART = 7
SEARCH_INPUT = 8
MOOD_TAG = 9
QUOTE_TEXT = 10
GENRE_FICTION = 11
GENRE_SCIENCE = 12
GENRE_PHILOSOPHY = 13
GENRE_PSYCHOLOGY = 14
GENRE_HISTORY = 15

# Genre to color pair mapping — every genre in categories.GENRES needs an entry
# or its books render colorless on the shelf and detail badge.
GENRE_COLORS = {
    "motivation": GENRE_MOTIVATION,
    "startup": GENRE_STARTUP,
    "romance": GENRE_ROMANCE,
    "fiction": GENRE_FICTION,
    "science": GENRE_SCIENCE,
    "philosophy": GENRE_PHILOSOPHY,
    "psychology": GENRE_PSYCHOLOGY,
    "history": GENRE_HISTORY,
}


def init_colors():
    """Initialize curses color pairs."""
    curses.start_color()
    curses.use_default_colors()

    curses.init_pair(SHELF_FRAME, curses.COLOR_CYAN, -1)
    curses.init_pair(TITLE_HIGHLIGHT, curses.COLOR_YELLOW, -1)
    curses.init_pair(BODY_TEXT, curses.COLOR_WHITE, -1)
    curses.init_pair(GENRE_MOTIVATION, curses.COLOR_GREEN, -1)
    curses.init_pair(GENRE_ROMANCE, curses.COLOR_MAGENTA, -1)
    curses.init_pair(GENRE_STARTUP, curses.COLOR_BLUE, -1)
    curses.init_pair(FAVORITE_HEART, curses.COLOR_RED, -1)
    curses.init_pair(SEARCH_INPUT, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(MOOD_TAG, curses.COLOR_CYAN, -1)
    curses.init_pair(QUOTE_TEXT, curses.COLOR_WHITE, -1)

    # Extended-palette hues keep all 8 genres distinct; basic-color fallbacks
    # for terminals without 256-color support.
    extended = curses.COLORS >= 256
    curses.init_pair(GENRE_FICTION, curses.COLOR_CYAN, -1)
    curses.init_pair(GENRE_SCIENCE, curses.COLOR_YELLOW, -1)
    curses.init_pair(GENRE_PHILOSOPHY, 183 if extended else curses.COLOR_WHITE, -1)
    curses.init_pair(GENRE_PSYCHOLOGY, 208 if extended else curses.COLOR_RED, -1)
    curses.init_pair(GENRE_HISTORY, 108 if extended else curses.COLOR_WHITE, -1)
