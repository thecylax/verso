import uuid

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import not_found
from app.models import Document, User
from app.routers.folders import get_owned_folder
from app.serializers import document_out, document_summary_out
from app.services.bible import ChapterFetcher, build_passages, get_bible_client
from app.services.titles import TITLE_MAX, effective_title
from app.sqltypes import utcnow

router = APIRouter(prefix="/api/documents", tags=["documents"])

CONTENT_MAX = 200_000
DOCUMENT_NOT_FOUND = "Nota não encontrada."


def check_title(value: str | None) -> str | None:
    if value is not None and len(value.strip()) > TITLE_MAX:
        raise ValueError(f"O título pode ter no máximo {TITLE_MAX} caracteres.")
    return value


def check_content(value: str | None) -> str | None:
    if value is not None and len(value) > CONTENT_MAX:
        raise ValueError("A nota pode ter no máximo 200.000 caracteres.")
    return value


class DocumentCreateIn(BaseModel):
    folder_id: uuid.UUID | None = None
    title: str = ""
    content_md: str = ""

    @field_validator("title")
    @classmethod
    def _title(cls, value: str) -> str:
        return check_title(value) or ""

    @field_validator("content_md")
    @classmethod
    def _content(cls, value: str) -> str:
        return check_content(value) or ""


class DocumentUpdateIn(BaseModel):
    title: str | None = None
    content_md: str | None = None

    @field_validator("title")
    @classmethod
    def _title(cls, value: str | None) -> str | None:
        return check_title(value)

    @field_validator("content_md")
    @classmethod
    def _content(cls, value: str | None) -> str | None:
        return check_content(value)

    @model_validator(mode="after")
    def _at_least_one(self) -> "DocumentUpdateIn":
        if self.title is None and self.content_md is None:
            raise ValueError("Envie título ou conteúdo.")
        return self


def get_owned_document(db: Session, user: User, document_id: uuid.UUID) -> Document:
    document = db.scalar(select(Document).where(Document.id == document_id, Document.user_id == user.id))
    if document is None:
        raise not_found(DOCUMENT_NOT_FOUND)
    return document


@router.get("")
def list_documents(
    folder_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if folder_id is not None:
        get_owned_folder(db, user, folder_id)
        where_folder = Document.folder_id == folder_id
    else:
        where_folder = Document.folder_id.is_(None)
    documents = db.scalars(
        select(Document)
        .where(Document.user_id == user.id, where_folder)
        .order_by(Document.created_at.desc(), Document.id)
    ).all()
    return {"documents": [document_summary_out(d) for d in documents]}


@router.post("", status_code=201)
def create_document(
    body: DocumentCreateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    bible: ChapterFetcher | None = Depends(get_bible_client),
) -> dict:
    if body.folder_id is not None:
        get_owned_folder(db, user, body.folder_id)
    document = Document(
        user_id=user.id,
        folder_id=body.folder_id,
        title=effective_title(body.title, body.content_md),
        content_md=body.content_md,
        passages=build_passages(db, body.content_md, user.bible_version, bible).passages,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document_out(document)


@router.get("/{document_id}")
def get_document(document_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    return document_out(get_owned_document(db, user, document_id))


@router.patch("/{document_id}")
def update_document(
    document_id: uuid.UUID,
    body: DocumentUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    bible: ChapterFetcher | None = Depends(get_bible_client),
) -> dict:
    document = get_owned_document(db, user, document_id)
    if body.content_md is not None and body.content_md != document.content_md:
        document.content_md = body.content_md
        document.passages = build_passages(
            db, document.content_md, user.bible_version, bible, previous=document.passages
        ).passages
    if body.title is not None:
        document.title = effective_title(body.title, document.content_md)
    document.updated_at = utcnow()
    db.commit()
    db.refresh(document)
    return document_out(document)


@router.post("/{document_id}/passages/refresh")
def refresh_passages(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    bible: ChapterFetcher | None = Depends(get_bible_client),
) -> dict:
    document = get_owned_document(db, user, document_id)
    result = build_passages(
        db, document.content_md, user.bible_version, bible, previous=document.passages, retry_failed=True
    )
    if result.passages != document.passages:
        document.passages = result.passages
        db.commit()
        db.refresh(document)
    return {"document": document_out(document), "refresh": {"updated": result.updated, "failed": result.failed}}


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    db.delete(get_owned_document(db, user, document_id))
    db.commit()
    return Response(status_code=204)
