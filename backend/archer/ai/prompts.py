"""
Prompt loading.

Prompts live in `prompts/*.md` at the repository root rather than inline in
Python. They are the part of this system most likely to change, most likely to
change behaviour when they do, and least readable buried in a source file. As
files they can be reviewed, diffed and versioned like anything else, and the
evaluation suite can attribute a change in accuracy to a change in a prompt.

Substitution is deliberately dumb: a literal replace of {{PLACEHOLDER}}
tokens. str.format and string.Template both assign meaning to characters that
appear naturally in these prompts - braces in JSON-ish examples, percent signs
in STRFTIME format strings, dollars in currency. A plain replace has no syntax
to collide with, which matters when the text being substituted is user input.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from ..core.paths import BASE_DIR


def _resolve_prompts_dir() -> Path:
    """
    Locate the prompts directory across both layouts, as with the frontend:
    /app/prompts in the container, <repo>/prompts locally.
    """
    candidates = [BASE_DIR / "prompts", BASE_DIR.parent / "prompts"]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]


PROMPTS_DIR = _resolve_prompts_dir()


def _strip_front_matter(text: str) -> str:
    """
    Remove the YAML front matter block used to record prompt metadata.

    The metadata is for humans and for the changelog; the model should never
    see it. Front matter is only stripped when the file actually opens with a
    delimiter, so a prompt without one is passed through untouched.
    """
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return text
    return parts[2].lstrip("\n")


@lru_cache(maxsize=None)
def load_prompt(name: str) -> str:
    """
    Read a prompt by name, without its front matter.

    Trailing whitespace is preserved deliberately, and this is not a detail.
    The SQL prompt ends with the user's question followed by a newline, and
    that newline is what tells the model to start a new line - with SQL on it.
    Stripping it made the model continue the question instead, and the suite
    went from 89% to 11% with every case reporting "no SQL produced". Only
    leading newlines left over from the front matter delimiter are removed.

    Cached: prompts do not change while the process runs, and re-reading a file
    on every request would put disk I/O in the path of every question.
    """
    path = PROMPTS_DIR / f"{name}.md"
    return _strip_front_matter(path.read_text(encoding="utf-8")).lstrip("\n")


def render(name: str, **values: str) -> str:
    """
    Load a prompt and substitute {{PLACEHOLDER}} tokens.

    Raises if a placeholder is left unsubstituted. A prompt silently sent to a
    model with a literal {{USER_QUERY}} in it is a bug that produces confident
    nonsense rather than an error, so it is worth failing loudly instead.
    """
    text = load_prompt(name)
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)

    if "{{" in text:
        leftover = text[text.index("{{") : text.index("{{") + 40]
        raise ValueError(f"Unsubstituted placeholder in prompt '{name}': {leftover!r}")

    return text
