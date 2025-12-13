"""Add document_analysis table

Revision ID: 002_document_analysis
Revises: 001_initial
Create Date: 2025-12-12 19:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = "002_document_analysis"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # Create document_analysis table
    op.create_table(
        "document_analysis",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("s3_key", sa.String(length=500), nullable=False),
        sa.Column("s3_bucket", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column(
            "classification",
            sa.Enum("FACTURA", "INFORMACION", name="documentclassification"),
            nullable=False,
        ),
        sa.Column("extracted_data", mssql.JSON(), nullable=True),
        sa.Column("vendor_name", sa.String(length=255), nullable=True),
        sa.Column("vendor_address", sa.Text(), nullable=True),
        sa.Column("client_name", sa.String(length=255), nullable=True),
        sa.Column("client_address", sa.Text(), nullable=True),
        sa.Column("invoice_number", sa.String(length=100), nullable=True),
        sa.Column("invoice_date", sa.String(length=50), nullable=True),
        sa.Column("invoice_total", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("sentiment", sa.String(length=50), nullable=True),
        sa.Column("full_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("GETDATE()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_document_analysis_id"), "document_analysis", ["id"], unique=False
    )


def downgrade():
    op.drop_index(op.f("ix_document_analysis_id"), table_name="document_analysis")
    op.drop_table("document_analysis")
    op.execute("DROP TYPE documentclassification")
