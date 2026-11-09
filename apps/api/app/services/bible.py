"""Captura de versículos: na criação, nas edições (só citações novas) e na atualização ao abrir a nota."""

from dataclasses import dataclass
from typing import Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session

from app.books import BOOKS_BY_ABBREV
from app.config import settings
from app.models import BibleChapterCache
from app.services.citations import parse_citations

MAX_RESOLVED = 40
TIMEOUT_SECONDS = 8.0
RETRYABLE_ERRORS = frozenset({"upstream_unavailable", "rate_limited", "bible_not_configured"})


class BibleError(Exception):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class ChapterFetcher(Protocol):
    def fetch_chapter(self, version: str, abbrev: str, chapter: int) -> list[dict]: ...


def _normalize_verses(payload: object) -> list[dict]:
    if not isinstance(payload, dict) or not isinstance(payload.get("verses"), list):
        raise BibleError("upstream_unavailable")
    verses = []
    for item in payload["verses"]:
        if not isinstance(item, dict):
            raise BibleError("upstream_unavailable")
        number, text = item.get("number"), item.get("text")
        if not isinstance(number, int) or not isinstance(text, str):
            raise BibleError("upstream_unavailable")
        verses.append({"number": number, "text": text})
    if not verses:
        raise BibleError("not_found")
    return sorted(verses, key=lambda verse: verse["number"])


class BibleClient:
    def __init__(self, base_url: str, token: str = "", transport: httpx.BaseTransport | None = None):
        self._base_url = base_url.rstrip("/")
        self._headers = {"Accept": "application/json"}
        if token:
            self._headers["Authorization"] = f"Bearer {token}"
        self._transport = transport

    def fetch_chapter(self, version: str, abbrev: str, chapter: int) -> list[dict]:
        url = f"{self._base_url}/verses/{version}/{abbrev}/{chapter}"
        with httpx.Client(timeout=TIMEOUT_SECONDS, transport=self._transport) as client:
            response = None
            for attempt in range(2):
                try:
                    response = client.get(url, headers=self._headers)
                    break
                except httpx.ConnectError:
                    if attempt == 1:
                        raise BibleError("upstream_unavailable")
                except httpx.HTTPError:
                    raise BibleError("upstream_unavailable")
        assert response is not None
        if response.status_code in (409, 429):
            raise BibleError("rate_limited")
        if response.status_code in (400, 404):
            raise BibleError("not_found")
        if response.status_code != 200:
            raise BibleError("upstream_unavailable")
        try:
            payload = response.json()
        except ValueError:
            raise BibleError("upstream_unavailable")
        return _normalize_verses(payload)


def get_bible_client() -> ChapterFetcher | None:
    # O token é opcional: sem ele o provedor responde com limite de requisições menor.
    if not settings.bible_api_base_url:
        return None
    return BibleClient(settings.bible_api_base_url, settings.bible_api_token)


def passage_key(passage: dict) -> tuple:
    return (passage["version"], passage["abbrev"], passage["chapter"], passage["start"], passage["end"])


def is_pending(passage: dict) -> bool:
    return passage.get("error") in RETRYABLE_ERRORS


@dataclass
class PassagesResult:
    passages: list[dict]
    updated: int = 0
    failed: int = 0


def slice_verses(verses: list[dict], start: int | None, end: int | None) -> list[dict]:
    ordered = sorted(verses, key=lambda verse: verse["number"])
    if start is None:
        return ordered
    if end is None:
        end = start
    if end < start:
        start, end = end, start
    return [verse for verse in ordered if start <= verse["number"] <= end]


def _load_chapter(
    db: Session, client: ChapterFetcher, version: str, abbrev: str, chapter: int
) -> list[dict]:
    cached = db.scalar(
        select(BibleChapterCache).where(
            BibleChapterCache.version == version,
            BibleChapterCache.abbrev == abbrev,
            BibleChapterCache.chapter == chapter,
        )
    )
    if cached is not None:
        return cached.verses
    verses = client.fetch_chapter(version, abbrev, chapter)
    insert = sqlite.insert if db.get_bind().dialect.name == "sqlite" else postgresql.insert
    db.execute(
        insert(BibleChapterCache)
        .values(version=version, abbrev=abbrev, chapter=chapter, verses=verses)
        .on_conflict_do_nothing()
    )
    return verses


def _reusable(previous: dict | None, retry_failed: bool) -> bool:
    if previous is None:
        return False
    error = previous.get("error")
    if error is None or error == "not_found":
        return True
    return error in RETRYABLE_ERRORS and not retry_failed


def build_passages(
    db: Session,
    content_md: str,
    default_version: str,
    client: ChapterFetcher | None,
    previous: list[dict] | None = None,
    retry_failed: bool = False,
) -> PassagesResult:
    """Passagens das citações atuais. As já capturadas são reaproveitadas; só as novas (e, com
    `retry_failed`, as que falharam por motivo temporário) vão ao provedor."""
    known = {passage_key(passage): passage for passage in previous or []}
    result = PassagesResult(passages=[])
    passages = result.passages
    seen: set[tuple] = set()
    chapters: dict[tuple[str, str, int], list[dict] | BibleError] = {}

    for citation in parse_citations(content_md):
        version = citation.version or default_version
        key = (version, citation.abbrev, citation.chapter, citation.start, citation.end)
        if key in seen:
            continue
        seen.add(key)

        earlier = known.get(key)
        if _reusable(earlier, retry_failed) and len(passages) < MAX_RESOLVED:
            passages.append(earlier)
            if is_pending(earlier):
                result.failed += 1
            continue
        retrying = earlier is not None and is_pending(earlier)

        book = BOOKS_BY_ABBREV.get(citation.abbrev)
        passage = {
            "version": version,
            "abbrev": citation.abbrev,
            "chapter": citation.chapter,
            "start": citation.start,
            "end": citation.end,
            "book_name": book["name"] if book else "",
            "verses": [],
            "error": None,
        }
        passages.append(passage)

        if book is None or not 1 <= citation.chapter <= book["chapters"]:
            passage["error"] = "invalid_reference"
            continue
        if len(passages) > MAX_RESOLVED:
            passage["error"] = "too_many"
            continue
        if client is None:
            passage["error"] = "bible_not_configured"
            result.failed += 1
            continue

        chapter_key = (version, citation.abbrev, citation.chapter)
        if chapter_key not in chapters:
            try:
                chapters[chapter_key] = _load_chapter(db, client, *chapter_key)
            except BibleError as error:
                chapters[chapter_key] = error
        loaded = chapters[chapter_key]
        if isinstance(loaded, BibleError):
            passage["error"] = loaded.code
            if is_pending(passage):
                result.failed += 1
            continue
        verses = slice_verses(loaded, citation.start, citation.end)
        if verses:
            passage["verses"] = verses
            if retrying:
                result.updated += 1
        else:
            passage["error"] = "not_found"

    return result
