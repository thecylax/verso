import uuid

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, field_validator
from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user
from app.errors import conflict, not_found, validation_error
from app.models import Document, Folder, User
from app.serializers import folder_out

router = APIRouter(prefix="/api/folders", tags=["folders"])

MAX_DEPTH = 20
FOLDER_NOT_FOUND = "Pasta não encontrada."
DUPLICATE_NAME = "Já existe uma pasta com este nome aqui."


def check_folder_name(value: str) -> str:
    value = value.strip()
    if not 1 <= len(value) <= 80:
        raise ValueError("O nome da pasta deve ter de 1 a 80 caracteres.")
    return value


class FolderUpdateIn(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        return check_folder_name(value)


class FolderCreateIn(FolderUpdateIn):
    parent_id: uuid.UUID | None = None


def get_owned_folder(db: Session, user: User, folder_id: uuid.UUID) -> Folder:
    folder = db.scalar(select(Folder).where(Folder.id == folder_id, Folder.user_id == user.id))
    if folder is None:
        raise not_found(FOLDER_NOT_FOUND)
    return folder


def ancestors(db: Session, folder: Folder) -> list[Folder]:
    """Trilha da raiz até a pasta, inclusive."""
    chain = [folder]
    current = folder
    while current.parent_id is not None and len(chain) <= MAX_DEPTH:
        parent = db.scalar(
            select(Folder).where(Folder.id == current.parent_id, Folder.user_id == folder.user_id)
        )
        if parent is None:
            break
        chain.append(parent)
        current = parent
    chain.reverse()
    return chain


@router.get("")
def list_folders(
    parent_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    breadcrumb: list[dict] = []
    if parent_id is not None:
        parent = get_owned_folder(db, user, parent_id)
        breadcrumb = [{"id": str(f.id), "name": f.name} for f in ancestors(db, parent)]
        where_parent = Folder.parent_id == parent_id
    else:
        where_parent = Folder.parent_id.is_(None)
    folders = db.scalars(
        select(Folder).where(Folder.user_id == user.id, where_parent).order_by(func.lower(Folder.name))
    ).all()
    return {"folders": [folder_out(f) for f in folders], "breadcrumb": breadcrumb}


@router.post("", status_code=201)
def create_folder(body: FolderCreateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    if body.parent_id is not None:
        parent = get_owned_folder(db, user, body.parent_id)
        if len(ancestors(db, parent)) + 1 > MAX_DEPTH:
            raise validation_error(f"Limite de {MAX_DEPTH} níveis de pastas atingido.")
    folder = Folder(user_id=user.id, parent_id=body.parent_id, name=body.name)
    db.add(folder)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict(DUPLICATE_NAME)
    db.refresh(folder)
    return folder_out(folder)


@router.patch("/{folder_id}")
def rename_folder(
    folder_id: uuid.UUID,
    body: FolderUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    folder = get_owned_folder(db, user, folder_id)
    folder.name = body.name
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise conflict(DUPLICATE_NAME)
    return folder_out(folder)


@router.delete("/{folder_id}", status_code=204)
def delete_folder(folder_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    folder = get_owned_folder(db, user, folder_id)
    has_children = db.scalar(select(exists().where(Folder.parent_id == folder.id)))
    has_documents = db.scalar(select(exists().where(Document.folder_id == folder.id)))
    if has_children or has_documents:
        raise conflict("Esvazie a pasta antes de apagá-la.")
    db.delete(folder)
    db.commit()
    return Response(status_code=204)
