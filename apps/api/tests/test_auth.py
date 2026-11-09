from tests.conftest import PASSWORD, register

INVALID_LOGIN = "E-mail ou senha incorretos."


def test_register_sets_http_only_cookie_and_returns_person(client):
    response = register(client, email="  Ana@Igreja.ORG ")
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@igreja.org"
    assert body["bible_version"] == "nvi"
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
    response = register(make_client(), email="ANA@igreja.org")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"
    assert "conta" in response.json()["error"]["message"]


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
    for method, path in [("get", "/api/auth/me"), ("get", "/api/folders"), ("get", "/api/documents"), ("post", "/api/auth/logout")]:
        response = getattr(client, method)(path)
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "unauthorized"


def test_update_bible_version(client):
    register(client)
    response = client.patch("/api/auth/me", json={"bible_version": "acf"})
    assert response.status_code == 200
    assert response.json()["bible_version"] == "acf"
    assert client.patch("/api/auth/me", json={"bible_version": "ACF!"}).status_code == 422
