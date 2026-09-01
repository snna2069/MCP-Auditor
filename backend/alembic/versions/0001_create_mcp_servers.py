"""create mcp_servers table

Revision ID: 0001_create_mcp_servers
Revises:
Create Date: 2026-09-01

"""
import sqlalchemy as sa
from alembic import op

revision = "0001_create_mcp_servers"
down_revision = None
branch_labels = None
depends_on = None

SOURCE_TYPE_VALUES = (
    "LOCAL_COMMAND",
    "HTTP",
    "SSE",
    "PACKAGE",
    "MANUAL_CONFIGURATION",
)


def upgrade() -> None:
    op.create_table(
        "mcp_servers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum(
                *SOURCE_TYPE_VALUES,
                name="mcp_server_source_type",
                native_enum=False,
                length=50,
            ),
            nullable=False,
        ),
        sa.Column("connection_config_encrypted", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_mcp_servers_name"), "mcp_servers", ["name"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_mcp_servers_name"), table_name="mcp_servers")
    op.drop_table("mcp_servers")
