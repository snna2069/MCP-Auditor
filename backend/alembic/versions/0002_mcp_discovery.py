"""add discovery status columns and mcp_server_tools table

Revision ID: 0002_mcp_discovery
Revises: 0001_create_mcp_servers
Create Date: 2026-09-01

"""
import sqlalchemy as sa
from alembic import op

revision = "0002_mcp_discovery"
down_revision = "0001_create_mcp_servers"
branch_labels = None
depends_on = None

DISCOVERY_STATUS_VALUES = ("SUCCESS", "FAILED")


def upgrade() -> None:
    op.add_column(
        "mcp_servers",
        sa.Column(
            "last_discovery_status",
            sa.Enum(
                *DISCOVERY_STATUS_VALUES,
                name="mcp_server_discovery_status",
                native_enum=False,
                length=20,
            ),
            nullable=True,
        ),
    )
    op.add_column(
        "mcp_servers",
        sa.Column("last_discovered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "mcp_servers",
        sa.Column("last_discovery_error", sa.Text(), nullable=True),
    )

    op.create_table(
        "mcp_server_tools",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("server_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("input_schema", sa.JSON(), nullable=False),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("annotations", sa.JSON(), nullable=True),
        sa.Column(
            "discovered_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["server_id"], ["mcp_servers.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "server_id", "name", name="uq_mcp_server_tools_server_name"
        ),
    )
    op.create_index(
        op.f("ix_mcp_server_tools_server_id"),
        "mcp_server_tools",
        ["server_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_mcp_server_tools_server_id"), table_name="mcp_server_tools")
    op.drop_table("mcp_server_tools")
    op.drop_column("mcp_servers", "last_discovery_error")
    op.drop_column("mcp_servers", "last_discovered_at")
    op.drop_column("mcp_servers", "last_discovery_status")
