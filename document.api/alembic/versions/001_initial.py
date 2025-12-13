"""Initial migration

Revision ID: 001_initial
Revises:
Create Date: 2025-12-12 19:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "user", "anonymous", name="userrole"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("GETDATE()"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(
        "ix_users_email_notnull",
        "users",
        ["email"],
        unique=True,
        mssql_where="email IS NOT NULL",
    )

    # Create file_uploads table
    op.create_table(
        "file_uploads",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("s3_key", sa.String(length=500), nullable=False),
        sa.Column("s3_bucket", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Integer(), nullable=False),
        sa.Column("param1", sa.String(length=255), nullable=True),
        sa.Column("param2", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("GETDATE()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_file_uploads_id"), "file_uploads", ["id"], unique=False)


def downgrade():
    op.drop_index(op.f("ix_file_uploads_id"), table_name="file_uploads")
    op.drop_table("file_uploads")
    op.drop_index("ix_users_email_notnull", table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE userrole")
