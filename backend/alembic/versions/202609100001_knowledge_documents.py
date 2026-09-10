"""Persist and isolate uploaded knowledge documents."""
from alembic import op
import sqlalchemy as sa

revision = "202609100001"
down_revision = "202607220001"
branch_labels = None
depends_on = None


def upgrade():
    if "knowledge_documents" not in sa.inspect(op.get_bind()).get_table_names():
        op.create_table(
            "knowledge_documents",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("owner", sa.String(32), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
        )
        op.create_index("ix_knowledge_documents_owner", "knowledge_documents", ["owner"])


def downgrade():
    op.drop_table("knowledge_documents")
