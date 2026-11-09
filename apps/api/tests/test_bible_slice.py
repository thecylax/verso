import httpx
import pytest

from app.main import app
from app.services.bible import BibleClient, BibleError, get_bible_client, slice_verses
from tests.conftest import register


class FakeBible:
    """Capítulo sintético: três versículos com texto "v1", "v2", "v3"."""

    def __init__(self, first: int = 1, error: str | None = None):
        self.first = first
        self.error = error
        self.calls: list[tuple[str, str, int]] = []

    def fetch_chapter(self, version: str, abbrev: str, chapter: int) -> list[dict]:
        self.calls.append((version, abbrev, chapter))
        if self.error:
            raise BibleError(self.error)
        return [{"number": self.first + i, "text": f"v{i + 1}"} for i in range(3)]


class ForbiddenBible:
    def fetch_chapter(self, *args):
        raise AssertionError("o provedor não deveria ser chamado aqui")


@pytest.fixture
def use_bible():
    def install(fake):
        app.dependency_overrides[get_bible_client] = lambda: fake
        return fake

    return install


@pytest.fixture
def person(client):
    register(client)
    return client


def create(client, content_md: str) -> dict:
    response = client.post("/api/documents", json={"content_md": content_md})
    assert response.status_code == 201
    return response.json()


def texts(passage: dict) -> list[str]:
    return [verse["text"] for verse in passage["verses"]]


def test_slice_verses_cases():
    verses = [{"number": 3, "text": "v3"}, {"number": 1, "text": "v1"}, {"number": 2, "text": "v2"}]
    assert [v["number"] for v in slice_verses(verses, None, None)] == [1, 2, 3]
    assert [v["number"] for v in slice_verses(verses, 2, 3)] == [2, 3]
    assert [v["number"] for v in slice_verses(verses, 3, 1)] == [1, 2, 3]
    assert [v["number"] for v in slice_verses(verses, 2, None)] == [2]


def test_whole_chapter(person, use_bible):
    use_bible(FakeBible())
    [passage] = create(person, "Sl 23")["passages"]
    assert passage == {
        "version": "nvi",
        "abbrev": "sl",
        "chapter": 23,
        "start": None,
        "end": None,
        "book_name": "Salmos",
        "verses": [{"number": 1, "text": "v1"}, {"number": 2, "text": "v2"}, {"number": 3, "text": "v3"}],
        "error": None,
    }


def test_range_2_to_3(person, use_bible):
    use_bible(FakeBible())
    [passage] = create(person, "Sl 23:2-3")["passages"]
    assert (passage["start"], passage["end"], texts(passage)) == (2, 3, ["v2", "v3"])


def test_reversed_range_is_stored_swapped(person, use_bible):
    use_bible(FakeBible())
    [passage] = create(person, "Sl 23:3-1")["passages"]
    assert (passage["start"], passage["end"], texts(passage)) == (1, 3, ["v1", "v2", "v3"])


def test_single_verse(person, use_bible):
    use_bible(FakeBible())
    [passage] = create(person, "Sl 23:2")["passages"]
    assert (passage["start"], passage["end"], texts(passage)) == (2, 2, ["v2"])


def test_same_chapter_is_fetched_once(person, use_bible):
    fake = use_bible(FakeBible())
    passages = create(person, "Sl 23:1 e depois Sl 23:2-3")["passages"]
    assert [texts(p) for p in passages] == [["v1"], ["v2", "v3"]]
    assert fake.calls == [("nvi", "sl", 23)]


def test_john_3_16_18_read_once_and_reused_on_edit(person, use_bible):
    fake = use_bible(FakeBible(first=16))
    note = create(person, "# Graça\n\nJoão 3:16-18")
    [passage] = note["passages"]
    assert texts(passage) == ["v1", "v2", "v3"]
    assert [v["number"] for v in passage["verses"]] == [16, 17, 18]
    assert fake.calls == [("nvi", "jo", 3)]
    assert note["passages_pending"] is False

    use_bible(ForbiddenBible())
    opened = person.get(f"/api/documents/{note['id']}").json()
    assert opened["passages"] == note["passages"]
    assert person.patch(f"/api/documents/{note['id']}", json={"title": "Outro"}).json()["passages"] == note["passages"]

    fake = use_bible(FakeBible())
    patched = person.patch(
        f"/api/documents/{note['id']}", json={"content_md": "# Graça\n\nJoão 3:16-18\n\nSl 23"}
    ).json()
    assert patched["passages"][0] == passage
    assert texts(patched["passages"][1]) == ["v1", "v2", "v3"]
    assert fake.calls == [("nvi", "sl", 23)]


def test_edit_drops_removed_citations(person, use_bible):
    use_bible(FakeBible())
    note = create(person, "Sl 23 e Gn 1:1")
    patched = person.patch(f"/api/documents/{note['id']}", json={"content_md": "Gn 1:1"}).json()
    assert [p["abbrev"] for p in patched["passages"]] == ["gn"]


def test_edit_does_not_retry_failed_passages(person, use_bible):
    use_bible(FakeBible(error="upstream_unavailable"))
    note = create(person, "Gn 1:1")
    assert note["passages_pending"] is True

    fake = use_bible(FakeBible())
    patched = person.patch(f"/api/documents/{note['id']}", json={"content_md": "Gn 1:1 hoje"}).json()
    assert patched["passages"][0]["error"] == "upstream_unavailable"
    assert fake.calls == []


def test_refresh_retries_failed_passages(person, use_bible):
    use_bible(FakeBible(error="rate_limited"))
    note = create(person, "Gn 1:1 e Sl 23:2")

    use_bible(FakeBible(error="upstream_unavailable"))
    still = person.post(f"/api/documents/{note['id']}/passages/refresh").json()
    assert still["refresh"] == {"updated": 0, "failed": 2}
    assert still["document"]["passages_pending"] is True

    fake = use_bible(FakeBible())
    done = person.post(f"/api/documents/{note['id']}/passages/refresh").json()
    assert done["refresh"] == {"updated": 2, "failed": 0}
    assert [texts(p) for p in done["document"]["passages"]] == [["v1"], ["v2"]]
    assert done["document"]["passages_pending"] is False
    assert sorted(fake.calls) == [("nvi", "gn", 1), ("nvi", "sl", 23)]
    assert person.get(f"/api/documents/{note['id']}").json()["passages"] == done["document"]["passages"]


def test_refresh_without_pending_does_not_call_provider(person, use_bible):
    use_bible(FakeBible())
    note = create(person, "Sl 23:1 e Xx 1:1")
    use_bible(ForbiddenBible())
    response = person.post(f"/api/documents/{note['id']}/passages/refresh").json()
    assert response["refresh"] == {"updated": 0, "failed": 0}
    assert response["document"]["passages"] == note["passages"]


def test_refresh_is_isolated_per_user(person, use_bible, make_client):
    use_bible(FakeBible())
    note = create(person, "Sl 23:1")
    other = make_client()
    register(other, email="outra@igreja.org")
    assert other.post(f"/api/documents/{note['id']}/passages/refresh").status_code == 404


def test_cache_avoids_second_fetch_in_later_note(person, use_bible):
    fake = use_bible(FakeBible())
    create(person, "Sl 23:1")
    create(person, "Sl 23:2")
    assert fake.calls == [("nvi", "sl", 23)]


def test_client_exists_without_token(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "bible_api_token", "")
    assert isinstance(get_bible_client(), BibleClient)
    monkeypatch.setattr(settings, "bible_api_base_url", "")
    assert get_bible_client() is None


def test_without_provider_note_is_created_with_error(person, use_bible):
    use_bible(None)
    note = create(person, "João 3:16")
    [passage] = note["passages"]
    assert passage["error"] == "bible_not_configured"
    assert passage["verses"] == []
    assert passage["book_name"] == "João"


def test_provider_failure_does_not_block(person, use_bible):
    use_bible(FakeBible(error="upstream_unavailable"))
    note = create(person, "Gn 1:1")
    assert note["passages"][0]["error"] == "upstream_unavailable"


def test_versions_explicit_and_account(person, use_bible):
    fake = use_bible(FakeBible())
    person.patch("/api/auth/me", json={"bible_version": "ara"})
    note = create(person, "Sl 23:1 e [[acf:sl:23:1-2]]")
    assert [(p["version"], p["start"], p["end"]) for p in note["passages"]] == [("ara", 1, 1), ("acf", 1, 2)]
    assert sorted(fake.calls) == [("acf", "sl", 23), ("ara", "sl", 23)]

    person.patch("/api/auth/me", json={"bible_version": "nvi"})
    assert person.get(f"/api/documents/{note['id']}").json()["passages"] == note["passages"]


def test_citations_in_code_are_ignored(person, use_bible):
    fake = use_bible(FakeBible())
    note = create(person, "`João 3:16`\n\n```\nSl 23\n```")
    assert note["passages"] == []
    assert fake.calls == []


def test_empty_slice_is_not_found(person, use_bible):
    use_bible(FakeBible())
    [passage] = create(person, "Sl 23:9")["passages"]
    assert passage["error"] == "not_found"


def test_more_than_40_citations(person, use_bible):
    fake = use_bible(FakeBible())
    content = " ".join(f"Sl {chapter}:1" for chapter in range(1, 43))
    passages = create(person, content)["passages"]
    assert len(passages) == 42
    assert [p["error"] for p in passages[40:]] == ["too_many", "too_many"]
    assert len(fake.calls) == 40


def test_http_client_contract():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"chapter": {"number": 23}, "verses": [{"number": 2, "text": "v2"}, {"number": 1, "text": "v1"}]})

    client = BibleClient("https://exemplo.test/api/", "segredo", transport=httpx.MockTransport(handler))
    assert client.fetch_chapter("nvi", "sl", 23) == [{"number": 1, "text": "v1"}, {"number": 2, "text": "v2"}]
    assert str(seen[0].url) == "https://exemplo.test/api/verses/nvi/sl/23"
    assert seen[0].headers["authorization"] == "Bearer segredo"
    assert seen[0].headers["accept"] == "application/json"

    anonymous = BibleClient("https://exemplo.test/api", transport=httpx.MockTransport(handler))
    anonymous.fetch_chapter("nvi", "sl", 23)
    assert "authorization" not in seen[1].headers


@pytest.mark.parametrize(
    ("status", "code"), [(409, "rate_limited"), (404, "not_found"), (500, "upstream_unavailable")]
)
def test_http_client_errors(status, code):
    client = BibleClient("https://exemplo.test/api", "t", transport=httpx.MockTransport(lambda r: httpx.Response(status)))
    with pytest.raises(BibleError) as error:
        client.fetch_chapter("nvi", "sl", 23)
    assert error.value.code == code


def test_http_client_retries_once_on_connection_error():
    attempts = []

    def handler(request):
        attempts.append(request)
        raise httpx.ConnectError("fora do ar", request=request)

    client = BibleClient("https://exemplo.test/api", "t", transport=httpx.MockTransport(handler))
    with pytest.raises(BibleError) as error:
        client.fetch_chapter("nvi", "sl", 23)
    assert error.value.code == "upstream_unavailable"
    assert len(attempts) == 2


def test_rate_limit_is_not_cached(person, use_bible):
    use_bible(FakeBible(error="rate_limited"))
    assert create(person, "Sl 23:1")["passages"][0]["error"] == "rate_limited"
    fake = use_bible(FakeBible())
    assert create(person, "Sl 23:1")["passages"][0]["error"] is None
    assert fake.calls == [("nvi", "sl", 23)]
