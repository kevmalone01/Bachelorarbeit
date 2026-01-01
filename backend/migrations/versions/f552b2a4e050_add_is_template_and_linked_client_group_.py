"""add_is_template_and_linked_client_group_ids_to_documents

Revision ID: f552b2a4e050
Revises: 91abc591ed5d
Create Date: 2025-11-13 21:30:09.510567

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f552b2a4e050'
down_revision = '91abc591ed5d'
branch_labels = None
depends_on = None


def upgrade():
    # Add is_template column to documents table
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_template', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('linked_client_group_ids', sa.JSON(), nullable=True))
    
    # Set default value for existing records
    op.execute("UPDATE documents SET is_template = 0 WHERE is_template IS NULL")


def downgrade():
    # Remove columns
    with op.batch_alter_table('documents', schema=None) as batch_op:
        batch_op.drop_column('linked_client_group_ids')
        batch_op.drop_column('is_template')
