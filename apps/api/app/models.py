import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import CHAR, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.sqltypes import JsonDocument, RootFolderId, UTCDateTime, Uuid, utcnow


def created_at_column() -> Mapped[datetime]:
    return mapped_column(UTCDateTime, nullable=False, default=utcnow, server_default=func.now())


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    email: Mapped[str] = mapped_column(String(254), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    bible_version: Mapped[str] = mapped_column(String(20), nullable=False, default="nvi", server_default="nvi")
    created_at: Mapped[datetime] = created_at_column()


class UserSession(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(CHAR(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, nullable=False)
    created_at: Mapped[datetime] = created_at_column()


class Folder(Base):
    __tablename__ = "folders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("folders.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = created_at_column()


Index("ix_folders_user_parent", Folder.user_id, Folder.parent_id)
Index(
    "uq_folders_siblings",
    Folder.user_id,
    func.coalesce(Folder.parent_id, RootFolderId()),
    func.lower(Folder.name),
    unique=True,
)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    folder_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("folders.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    passages: Mapped[list[dict[str, Any]]] = mapped_column(
        JsonDocument, nullable=False, default=list, server_default="[]"
    )
    created_at: Mapped[datetime] = created_at_column()
    updated_at: Mapped[datetime] = created_at_column()


Index("ix_documents_user_folder_created", Document.user_id, Document.folder_id, Document.created_at.desc())


class BibleChapterCache(Base):
    __tablename__ = "bible_chapter_cache"

    version: Mapped[str] = mapped_column(String(20), primary_key=True)
    abbrev: Mapped[str] = mapped_column(String(8), primary_key=True)
    chapter: Mapped[int] = mapped_column(Integer, primary_key=True)
    verses: Mapped[list[dict[str, Any]]] = mapped_column(JsonDocument, nullable=False)
    fetched_at: Mapped[datetime] = created_at_column()
