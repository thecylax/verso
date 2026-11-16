"""convites de cadastro

Revision ID: 0004
Revises: 0003
"""
import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("can_invite", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.execute(sa.text("UPDATE users SET can_invite = TRUE"))
    op.create_table(
        "invites",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("token_hash", sa.CHAR(64), nullable=False, unique=True),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_invites_created_by", "invites", ["created_by"])


def downgrade() -> None:
    op.drop_index("ix_invites_created_by", table_name="invites")
    op.drop_table("invites")
    op.drop_column("users", "can_invite")
