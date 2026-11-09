"""folders e documents

Revision ID: 0002
Revises: 0001
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    postgres = op.get_bind().dialect.name == "postgresql"
    root_folder_id = "'00000000-0000-0000-0000-000000000000'::uuid" if postgres else "'00000000000000000000000000000000'"

    op.create_table(
        "folders",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("parent_id", sa.Uuid(), sa.ForeignKey("folders.id"), nullable=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_folders_user_parent", "folders", ["user_id", "parent_id"])
    op.execute(
        "CREATE UNIQUE INDEX uq_folders_siblings ON folders "
        f"(user_id, coalesce(parent_id, {root_folder_id}), lower(name))"
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("folder_id", sa.Uuid(), sa.ForeignKey("folders.id"), nullable=True),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "passages",
            sa.JSON().with_variant(JSONB(), "postgresql"),
            nullable=False,
            server_default=sa.text("'[]'::jsonb" if postgres else "'[]'"),
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.execute(
        "CREATE INDEX ix_documents_user_folder_created ON documents (user_id, folder_id, created_at DESC)"
    )


def downgrade() -> None:
    op.drop_table("documents")
    op.drop_table("folders")
