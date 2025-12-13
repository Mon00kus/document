from alembic import op

# revision identifiers, used by Alembic
revision = "migration_replace_email_index"
down_revision = "not_previous_revision"
branch_labels = None
depends_on = None

def upgrade():
    # Eliminar índice único actual
    op.drop_index("ix_users_email", table_name="users")

    # Crear índice único filtrado (solo emails no nulos)
    op.create_index(
        "ix_users_email_notnull",
        "users",
        ["email"],
        unique=True,
        mssql_where="email IS NOT NULL"
    )

def downgrade():
    # Revertir cambios: eliminar índice filtrado y recrear el original
    op.drop_index("ix_users_email_notnull", table_name="users")
    op.create_index("ix_users_email", "users", ["email"], unique=True)