"""initial atoms demo schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-16
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("visitors", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.PrimaryKeyConstraint("id"))
    op.create_table("projects", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("owner_id", sa.String(length=36), nullable=False), sa.Column("name", sa.String(length=120), nullable=False), sa.Column("template_type", sa.String(length=32), nullable=False), sa.Column("prompt", sa.Text(), nullable=False), sa.Column("app_config", sa.JSON(), nullable=False), sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("share_token", sa.String(length=18), nullable=False), sa.Column("current_version", sa.Integer(), nullable=False, server_default="1"), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.ForeignKeyConstraint(["owner_id"], ["visitors.id"]), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("share_token"))
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"])
    op.create_index("ix_projects_share_token", "projects", ["share_token"])
    op.create_table("messages", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("project_id", sa.String(length=36), nullable=False), sa.Column("role", sa.String(length=16), nullable=False), sa.Column("agent", sa.String(length=64), nullable=True), sa.Column("content", sa.Text(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.ForeignKeyConstraint(["project_id"], ["projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_messages_project_id", "messages", ["project_id"])
    op.create_table("versions", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("project_id", sa.String(length=36), nullable=False), sa.Column("number", sa.Integer(), nullable=False), sa.Column("summary", sa.String(length=220), nullable=False), sa.Column("prompt", sa.Text(), nullable=False), sa.Column("app_config", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.ForeignKeyConstraint(["project_id"], ["projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_versions_project_id", "versions", ["project_id"])
    op.create_table("app_records", sa.Column("id", sa.String(length=36), nullable=False), sa.Column("project_id", sa.String(length=36), nullable=False), sa.Column("record_type", sa.String(length=32), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.ForeignKeyConstraint(["project_id"], ["projects.id"]), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_app_records_project_id", "app_records", ["project_id"])
    op.create_index("ix_app_records_record_type", "app_records", ["record_type"])


def downgrade() -> None:
    op.drop_table("app_records")
    op.drop_table("versions")
    op.drop_table("messages")
    op.drop_table("projects")
    op.drop_table("visitors")
