from alembic import op
import sqlalchemy as sa

revision = '004_event_logs'
#down_revision = '003_document_analysis'
down_revision = '003_file_uploads'
branch_labels = None
depends_on = None

def upgrade():
    pass

def downgrade():
    pass