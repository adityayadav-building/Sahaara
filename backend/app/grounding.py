"""Post-checks on model output: keep citations valid and strip anything that looks like an invented verse."""
from __future__ import annotations

import re

_DEVANAGARI_VERSE = re.compile(r"[^\n]*॥[^\n]*")  # double danda marks a Sanskrit verse; single । is a normal Hindi full stop
_REF = re.compile(r"\(?\b(?:bhagavad\s*)?gita\s*(?:chapter\s*)?\d{1,2}\s*[.:,]\s*\d{1,3}\)?|\bchapter\s*\d{1,2}\s*,?\s*verse\s*\d{1,3}",
                  re.IGNORECASE)


def sanitize(text: str) -> tuple[str, list[str]]:
    """Remove invented verse references / Sanskrit couplets. Returns (clean_text, issues)."""
    issues = []
    if _DEVANAGARI_VERSE.search(text):
        text = _DEVANAGARI_VERSE.sub("", text)
        issues.append("sanskrit_line_removed")
    if _REF.search(text):
        text = _REF.sub("", text)
        issues.append("verse_reference_removed")
    return re.sub(r"[ \t]{2,}", " ", text).strip(), issues


def valid_citations(cited: list[int], n_sources: int) -> list[int]:
    seen: list[int] = []
    for c in cited:
        if 1 <= c <= n_sources and c not in seen:
            seen.append(c)
    return seen
