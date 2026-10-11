"""Add stronger PostgreSQL-friendly constraints and indexes."""

from alembic import op

revision = "f96b0fa4d5b1"
down_revision = "9743b997d217"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index("ix_users_is_active", ["is_active"], unique=False)

    with op.batch_alter_table("trials", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "ck_trials_status_valid",
            "status IN ('active', 'recruiting', 'paused', 'completed', 'terminated')",
        )
        batch_op.create_index("ix_trials_status", ["status"], unique=False)

    with op.batch_alter_table("participants", schema=None) as batch_op:
        batch_op.create_check_constraint(
            "ck_participants_status_valid",
            "status IN ('active', 'completed', 'withdrawn')",
        )

    with op.batch_alter_table("audit_events", schema=None) as batch_op:
        batch_op.create_index(
            "ix_audit_events_action_outcome", ["action", "outcome"], unique=False
        )


def downgrade() -> None:
    with op.batch_alter_table("audit_events", schema=None) as batch_op:
        batch_op.drop_index("ix_audit_events_action_outcome")

    with op.batch_alter_table("participants", schema=None) as batch_op:
        batch_op.drop_constraint("ck_participants_status_valid", type_="check")

    with op.batch_alter_table("trials", schema=None) as batch_op:
        batch_op.drop_index("ix_trials_status")
        batch_op.drop_constraint("ck_trials_status_valid", type_="check")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index("ix_users_is_active")
