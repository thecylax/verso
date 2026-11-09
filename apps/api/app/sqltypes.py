from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import ColumnElement
from sqlalchemy.types import TypeDecorator

JsonDocument = JSON().with_variant(JSONB(), "postgresql")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UTCDateTime(TypeDecorator):
    """Sempre devolve datetime com fuso UTC; o SQLite guarda e lê sem fuso."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class RootFolderId(ColumnElement):
    """Valor de `coalesce(parent_id, ...)` no índice de irmãos, no formato do `Uuid` de cada banco."""

    type = Uuid()
    inherit_cache = True


@compiles(RootFolderId)
def _root_folder_id_default(element, compiler, **kw) -> str:
    return "'00000000000000000000000000000000'"


@compiles(RootFolderId, "postgresql")
def _root_folder_id_postgresql(element, compiler, **kw) -> str:
    return "'00000000-0000-0000-0000-000000000000'::uuid"


__all__ = ["JsonDocument", "RootFolderId", "UTCDateTime", "Uuid", "utcnow"]
