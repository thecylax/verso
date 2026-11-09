import os
from collections.abc import Callable, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL, make_url
from sqlalchemy.orm import sessionmaker

from app import models  # noqa: F401
from app.config import settings
from app.db import Base, get_db, make_engine
from app.main import app
from app.services.bible import get_bible_client

PASSWORD = "uma-senha-boa"


def _test_database_url(tmp_path_factory: pytest.TempPathFactory) -> URL:
    explicit = os.environ.get("TEST_DATABASE_URL")
    if explicit:
        return make_url(explicit)
    base = make_url(settings.database_url)
    if base.get_backend_name() == "sqlite":
        return base.set(database=str(tmp_path_factory.mktemp("db") / "verso_test.db"))
    return base.set(database=f"{base.database}_test")


def _ensure_postgres_database(url: URL) -> None:
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as connection:
        exists = connection.scalar(text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database})
        if not exists:
            connection.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def engine(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Engine]:
    url = _test_database_url(tmp_path_factory)
    if url.get_backend_name() == "postgresql":
        _ensure_postgres_database(url)

    test_engine = make_engine(url.render_as_string(hide_password=False))
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def session_factory(engine: Engine) -> Iterator[sessionmaker]:
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    yield factory
    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())


@pytest.fixture
def make_client(session_factory: sessionmaker) -> Iterator[Callable[[], TestClient]]:
    def override_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides.setdefault(get_bible_client, lambda: None)
    clients: list[TestClient] = []

    def factory() -> TestClient:
        client = TestClient(app)
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.close()
    app.dependency_overrides.clear()


@pytest.fixture
def client(make_client: Callable[[], TestClient]) -> TestClient:
    return make_client()


def register(client: TestClient, email: str = "ana@igreja.org", name: str = "Ana", password: str = PASSWORD):
    return client.post("/api/auth/register", json={"name": name, "email": email, "password": password})
