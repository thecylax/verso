from collections.abc import Iterator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _sqlite_lower(value: str | None) -> str | None:
    return value.lower() if isinstance(value, str) else value


def make_engine(url: str) -> Engine:
    if not url.startswith("sqlite"):
        return create_engine(url, pool_pre_ping=True)

    sqlite_engine = create_engine(url, connect_args={"check_same_thread": False})

    @event.listens_for(sqlite_engine, "connect")
    def _configure_sqlite(dbapi_connection, _record) -> None:
        # lower() nativo do SQLite só conhece ASCII; o índice de irmãos precisa de "É" == "é".
        dbapi_connection.create_function("lower", 1, _sqlite_lower, deterministic=True)
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.close()

    return sqlite_engine


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
