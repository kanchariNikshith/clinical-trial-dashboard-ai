"""Add rotating refresh-token storage for browser session persistence."""

from alembic import op
import sqlalchemy as sa

revision = "8e1d9a3f7f0c"
down_revision = "f96b0fa4d5b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("family_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("replaced_by_token_id", sa.String(length=36), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("refresh_tokens", schema=None) as batch_op:
        batch_op.create_index("ix_refresh_tokens_family_id", ["family_id"], unique=False)
        batch_op.create_index("ix_refresh_tokens_token_hash", ["token_hash"], unique=True)
        batch_op.create_index("ix_refresh_tokens_user_id", ["user_id"], unique=False)
        batch_op.create_index("ix_refresh_tokens_expires_at", ["expires_at"], unique=False)
        batch_op.create_index("ix_refresh_tokens_revoked_at", ["revoked_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("refresh_tokens", schema=None) as batch_op:
        batch_op.drop_index("ix_refresh_tokens_revoked_at")
        batch_op.drop_index("ix_refresh_tokens_expires_at")
        batch_op.drop_index("ix_refresh_tokens_user_id")
        batch_op.drop_index("ix_refresh_tokens_token_hash")
        batch_op.drop_index("ix_refresh_tokens_family_id")

    op.drop_table("refresh_tokens")
