"""add audits and audit_findings tables

Revision ID: 0003_audit_execution
Revises: 0002_mcp_discovery
Create Date: 2026-09-01

"""
import sqlalchemy as sa
from alembic import op

revision = "0003_audit_execution"
down_revision = "0002_mcp_discovery"
branch_labels = None
depends_on = None

AUDIT_STATUS_VALUES = ("PENDING", "RUNNING", "COMPLETED", "FAILED")
RISK_LEVEL_VALUES = ("LOW", "MODERATE", "HIGH", "CRITICAL")
AUDIT_CATEGORY_VALUES = (
    "TOOL_DEFINITION_QUALITY",
    "CAPABILITY_PERMISSION_RISK",
    "PROMPT_INJECTION_RISK",
    "HALLUCINATION_RELIABILITY_RISK",
    "SIDE_EFFECT_ANALYSIS",
)
SEVERITY_VALUES = ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")


def upgrade() -> None:
    op.create_table(
        "audits",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("server_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(*AUDIT_STATUS_VALUES, name="audit_status", native_enum=False, length=20),
            nullable=False,
        ),
        sa.Column("audit_version", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column(
            "risk_level",
            sa.Enum(
                *RISK_LEVEL_VALUES, name="audit_risk_level", native_enum=False, length=20
            ),
            nullable=True,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["server_id"], ["mcp_servers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audits_server_id"), "audits", ["server_id"], unique=False)

    op.create_table(
        "audit_findings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("audit_id", sa.Uuid(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                *AUDIT_CATEGORY_VALUES,
                name="audit_finding_category",
                native_enum=False,
                length=40,
            ),
            nullable=False,
        ),
        sa.Column(
            "severity",
            sa.Enum(
                *SEVERITY_VALUES, name="audit_finding_severity", native_enum=False, length=20
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("tool_name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_findings_audit_id"), "audit_findings", ["audit_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_findings_audit_id"), table_name="audit_findings")
    op.drop_table("audit_findings")
    op.drop_index(op.f("ix_audits_server_id"), table_name="audits")
    op.drop_table("audits")
