"""Hermes plugin registration for the standalone Bookshelf repository."""

from __future__ import annotations

from pathlib import Path
import sys


_PLUGIN_ROOT = Path(__file__).resolve().parent
if str(_PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_ROOT))


def _transform_llm_output(response_text: str, **_kwargs) -> str | None:
    """Append a due quote, or leave the completed response untouched."""
    try:
        from bookshelf.ambient import ambient_message

        message = ambient_message("hermes")
        if not message:
            return None
        return f"{response_text.rstrip()}\n\n{message}"
    except Exception:
        return None


def register(ctx) -> None:
    """Register the native Hermes hook and canonical Open Agent Skill."""
    ctx.register_hook("transform_llm_output", _transform_llm_output)
    skill = _PLUGIN_ROOT / "skills" / "bookshelf" / "SKILL.md"
    if skill.is_file():
        ctx.register_skill("bookshelf", skill)
