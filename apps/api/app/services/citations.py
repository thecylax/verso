"""Gramática de citações, espelho de apps/web/src/lib/citations.ts.

Python não tem \\p{L}; `[^\\W_]` (palavra Unicode sem sublinhado) cobre letras e dígitos.
"""

import re
from dataclasses import dataclass

from app.books import BOOKS, BOOKS_BY_ABBREV
from app.services.markdown import mask_fences

ALIAS_TO_ABBREV = {alias: book["abbrev"] for book in BOOKS for alias in book["aliases"]}
_ALIASES = sorted(ALIAS_TO_ABBREV, key=len, reverse=True)

EXPLICIT_RE = re.compile(
    r"\[\[([a-z0-9]{2,20}):([a-z0-9]{1,8}):([0-9]{1,3})(?::([0-9]{1,3})(?:-([0-9]{1,3}))?)?\]\]"
)
NATURAL_RE = re.compile(
    r"(?<![^\W_])("
    + "|".join(re.escape(alias) for alias in _ALIASES)
    + r")\.?(?![^\W_])\s*([0-9]{1,3})(?:\s*[:.]\s*([0-9]{1,3})(?:\s*[-–—]\s*([0-9]{1,3}))?)?"
)
CHAPTER_ONLY_END_RE = re.compile(r"[^\S\n]*(?:\n|\Z|[,.;!?)\]}”\"'])")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")


@dataclass(frozen=True)
class Citation:
    version: str | None
    abbrev: str
    chapter: int
    start: int | None
    end: int | None
    index: int


def _blank(match: re.Match[str]) -> str:
    return re.sub(r"[^\n]", " ", match.group(0))


def mask_code(markdown: str) -> str:
    masked = mask_fences(markdown)
    masked = INLINE_CODE_RE.sub(_blank, masked)
    return HTML_COMMENT_RE.sub(_blank, masked)


def _build(version: str | None, abbrev: str, chapter: int, start: int | None, end: int | None, index: int) -> Citation | None:
    book = BOOKS_BY_ABBREV.get(abbrev)
    if book is None or not 1 <= chapter <= book["chapters"]:
        return None
    if start is not None:
        if end is None:
            end = start
        if start < 1 or end < 1:
            return None
        if end < start:
            start, end = end, start
    else:
        end = None
    return Citation(version, abbrev, chapter, start, end, index)


def _num(value: str | None) -> int | None:
    return int(value) if value is not None else None


def parse_citations(markdown: str) -> list[Citation]:
    text = mask_code(markdown).lower()
    found: list[Citation] = []

    def take_explicit(match: re.Match[str]) -> str:
        citation = _build(
            match.group(1),
            match.group(2),
            int(match.group(3)),
            _num(match.group(4)),
            _num(match.group(5)),
            match.start(),
        )
        if citation:
            found.append(citation)
        return " " * len(match.group(0))

    text = EXPLICIT_RE.sub(take_explicit, text)

    for match in NATURAL_RE.finditer(text):
        verse = match.group(3)
        if verse is None and not CHAPTER_ONLY_END_RE.match(text, match.end()):
            continue
        citation = _build(
            None,
            ALIAS_TO_ABBREV[match.group(1)],
            int(match.group(2)),
            _num(verse),
            _num(match.group(4)),
            match.start(),
        )
        if citation:
            found.append(citation)

    found.sort(key=lambda c: c.index)
    seen: set[str] = set()
    unique: list[Citation] = []
    for citation in found:
        key = f"{citation.version or ''}|{citation.abbrev}|{citation.chapter}|{citation.start}|{citation.end}"
        if key not in seen:
            seen.add(key)
            unique.append(citation)
    return unique
