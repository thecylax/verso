"""bible_chapter_cache

Revision ID: 0003
Revises: 0002
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "bible_chapter_cache",
        sa.Column("version", sa.String(20), primary_key=True),
        sa.Column("abbrev", sa.String(8), primary_key=True),
        sa.Column("chapter", sa.Integer(), primary_key=True),
        sa.Column("verses", sa.JSON().with_variant(JSONB(), "postgresql"), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("bible_chapter_cache")
