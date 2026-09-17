"""add users + visitors.user_id

Revision ID: 0002_add_users
Revises: 0001_initial
Create Date: 2026-09-17
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_add_users"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=190), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # SQLite: batch mode for ALTER
    with op.batch_alter_table("visitors") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key("fk_visitors_user_id", "users", ["user_id"], ["id"])
        batch_op.create_index("ix_visitors_user_id", ["user_id"])


def downgrade() -> None:
    with op.batch_alter_table("visitors") as batch_op:
        batch_op.drop_index("ix_visitors_user_id")
        batch_op.drop_constraint("fk_visitors_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
