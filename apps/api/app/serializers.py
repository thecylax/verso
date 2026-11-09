from datetime import datetime, timezone

from app.models import Document, Folder, User
from app.services.bible import is_pending


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def user_out(user: User) -> dict:
    return {
        "id": str(user.id),
        "name": user.name,
        "email": user.email,
        "bible_version": user.bible_version,
    }


def folder_out(folder: Folder) -> dict:
    return {
        "id": str(folder.id),
        "name": folder.name,
        "parent_id": str(folder.parent_id) if folder.parent_id else None,
        "created_at": iso(folder.created_at),
    }


def document_summary_out(document: Document) -> dict:
    return {
        "id": str(document.id),
        "title": document.title,
        "folder_id": str(document.folder_id) if document.folder_id else None,
        "created_at": iso(document.created_at),
        "updated_at": iso(document.updated_at),
    }


def document_out(document: Document) -> dict:
    return {
        **document_summary_out(document),
        "content_md": document.content_md,
        "passages": document.passages,
        "passages_pending": any(is_pending(passage) for passage in document.passages),
    }
