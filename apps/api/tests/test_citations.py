import json
from pathlib import Path

import pytest

from app.books import BOOKS
from app.services.citations import parse_citations

POSITIVE = [
    ("João 3:16", (None, "jo", 3, 16, 16)),
    ("Jo 3.16", (None, "jo", 3, 16, 16)),
    ("João 3:16-18", (None, "jo", 3, 16, 18)),
    ("1 Coríntios 13:4-7", (None, "1co", 13, 4, 7)),
    ("1 Co 13:4", (None, "1co", 13, 4, 4)),
    ("1Co 13:4", (None, "1co", 13, 4, 4)),
    ("Sl 23", (None, "sl", 23, None, None)),
    ("Salmos 23:1", (None, "sl", 23, 1, 1)),
    ("Gn 1:1-3", (None, "gn", 1, 1, 3)),
    ("Jó 1:21", (None, "job", 1, 21, 21)),
    ("Job 1:21", (None, "job", 1, 21, 21)),
    ("leia João 3:16 hoje", (None, "jo", 3, 16, 16)),
    ("[[acf:sl:23:1-6]]", ("acf", "sl", 23, 1, 6)),
    ("[[nvi:sl:23]]", ("nvi", "sl", 23, None, None)),
    ("I João 1:9", (None, "1jo", 1, 9, 9)),
    ("2ª Timóteo 3:16", (None, "2tm", 3, 16, 16)),
    ("Sl. 23:1", (None, "sl", 23, 1, 1)),
    ("(Gn 1)", (None, "gn", 1, None, None)),
    ("João 3:16 e João 3:16", (None, "jo", 3, 16, 16)),
]

NEGATIVE = [
    "João 3 vezes",
    "`João 3:16`",
    "```\nJoão 3:16\n```",
    "Coríntios 13:4",
    "João 99:1",
]


@pytest.mark.parametrize(("text", "expected"), POSITIVE)
def test_positive_vectors(text, expected):
    result = parse_citations(text)
    assert len(result) == 1
    c = result[0]
    assert (c.version, c.abbrev, c.chapter, c.start, c.end) == expected


@pytest.mark.parametrize("text", NEGATIVE)
def test_negative_vectors(text):
    assert parse_citations(text) == []


def test_jo_is_john_not_job():
    assert [c.abbrev for c in parse_citations("Jo 3:16")] == ["jo"]


def test_books_catalog():
    assert len(BOOKS) == 66
    by_abbrev = {b["abbrev"]: b for b in BOOKS}
    assert by_abbrev["tt"]["chapters"] == 3
    assert by_abbrev["fm"]["chapters"] == 1


def test_books_match_front_catalog():
    books_ts = Path(__file__).resolve().parents[2] / "web" / "src" / "lib" / "books.ts"
    if not books_ts.exists():
        pytest.skip("apps/web não está disponível neste ambiente")
    source = books_ts.read_text(encoding="utf-8").replace("\r\n", "\n")
    start = source.index("export const BOOKS: Book[] = ") + len("export const BOOKS: Book[] = ")
    end = source.index("\n];", start) + 2
    front = json.loads(source[start:end].replace("},\n]", "}\n]"))
    assert [b["abbrev"] for b in front] == [b["abbrev"] for b in BOOKS]
    assert [b["chapters"] for b in front] == [b["chapters"] for b in BOOKS]
