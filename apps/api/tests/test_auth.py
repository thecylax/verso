from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models import Invite
from tests.conftest import PASSWORD, issue_invite, register

INVALID_LOGIN = "E-mail ou senha incorretos."


def test_register_sets_http_only_cookie_and_returns_person(client):
    response = register(client, email="  Ana@Igreja.ORG ")
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@igreja.org"
    assert body["bible_version"] == "nvi"
    assert body["can_invite"] is True
    cookie = response.headers["set-cookie"]
    assert cookie.startswith("session=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/" in cookie
    assert "Max-Age=2592000" in cookie
    assert client.get("/api/auth/me").json()["email"] == "ana@igreja.org"


def test_short_password_is_rejected(client):
    response = register(client, password="curta")
    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "validation_error",
        "message": "A senha precisa ter pelo menos 8 caracteres.",
    }
    assert "set-cookie" not in response.headers


def test_duplicate_email_ignores_case(client, make_client):
    assert register(client).status_code == 201
    token = issue_invite(client)
    response = register(make_client(), email="ANA@igreja.org", invite=token)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert "conta" in response.json()["error"]["message"]
    created = register(make_client(), email="bia@igreja.org", name="Bia", invite=token)
    assert created.status_code == 201
    assert created.json()["can_invite"] is False


def test_invalid_login_has_a_single_message(client, make_client):
    register(client)
    other = make_client()
    unknown = other.post("/api/auth/login", json={"email": "ninguem@igreja.org", "password": PASSWORD})
    wrong = other.post("/api/auth/login", json={"email": "ana@igreja.org", "password": "senha-errada"})
    for response in (unknown, wrong):
        assert response.status_code == 401
        assert response.json() == {"error": {"code": "unauthorized", "message": INVALID_LOGIN}}


def test_login_with_valid_credentials(client, make_client):
    register(client)
    other = make_client()
    response = other.post("/api/auth/login", json={"email": "ANA@igreja.org", "password": PASSWORD})
    assert response.status_code == 200
    assert other.get("/api/auth/me").status_code == 200


def test_logout_ends_session(client):
    register(client)
    token = client.cookies.get("session")
    response = client.post("/api/auth/logout")
    assert response.status_code == 204
    assert 'session=""' in response.headers["set-cookie"]
    assert client.get("/api/auth/me").status_code == 401
    client.cookies.set("session", token)
    assert client.get("/api/auth/me").status_code == 401


def test_requests_without_session_are_unauthorized(client):
    for method, path in [
        ("get", "/api/auth/me"),
        ("get", "/api/folders"),
        ("get", "/api/documents"),
        ("post", "/api/auth/logout"),
        ("post", "/api/auth/invites"),
    ]:
        response = getattr(client, method)(path)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"


def test_register_without_invite_is_forbidden_after_the_first_account(client, make_client):
    register(client)
    response = register(make_client(), email="bia@igreja.org", name="Bia")
    assert response.status_code == 403
    assert response.json()["error"] == {
        "code": "forbidden",
        "message": "Cadastro só é possível com um convite.",
    }


def test_invite_is_single_use(client, make_client):
    register(client)
    token = issue_invite(client)
    assert register(make_client(), email="bia@igreja.org", name="Bia", invite=token).status_code == 201
    again = register(make_client(), email="caio@igreja.org", name="Caio", invite=token)
    assert again.status_code == 403
    assert again.json()["error"]["message"] == "Convite inválido ou já utilizado."


def test_expired_invite_is_rejected(client, make_client, session_factory):
    register(client)
    token = issue_invite(client)
    db = session_factory()
    try:
        invite = db.scalar(select(Invite))
        assert invite is not None
        invite.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    finally:
        db.close()
    response = register(make_client(), email="bia@igreja.org", name="Bia", invite=token)
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Este convite expirou."


def test_invited_user_cannot_create_invites(client, make_client):
    register(client)
    other = make_client()
    assert register(other, email="bia@igreja.org", name="Bia", invite=issue_invite(client)).status_code == 201
    response = other.post("/api/auth/invites")
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Você não pode gerar convites."


def test_unknown_invite_is_rejected(client, make_client):
    register(client)
    preview = client.get("/api/auth/invites/nao-existe")
    assert preview.status_code == 403
    assert preview.json()["error"]["message"] == "Convite inválido ou já utilizado."
    response = register(make_client(), email="bia@igreja.org", name="Bia", invite="nao-existe")
    assert response.status_code == 403
    assert response.json()["error"]["message"] == "Convite inválido ou já utilizado."


def test_update_bible_version(client):
    register(client)
    response = client.patch("/api/auth/me", json={"bible_version": "acf"})
    assert response.status_code == 200
    assert response.json()["bible_version"] == "acf"
    assert client.patch("/api/auth/me", json={"bible_version": "ACF!"}).status_code == 422


def test_bootstrap_registration_requires_secret_and_is_single_use(client, make_client):
    without_secret = make_client().post(
        "/api/auth/register",
        json={"name": "Intruso", "email": "intruso@igreja.org", "password": PASSWORD},
    )
    assert without_secret.status_code == 403

    assert register(client).status_code == 201

    second_without_invite = make_client().post(
        "/api/auth/register",
        json={"name": "Outro", "email": "outro@igreja.org", "password": PASSWORD},
    )
    assert second_without_invite.status_code == 403
    assert second_without_invite.json()["error"]["message"] == "Cadastro só é possível com um convite."
