"""Add status and is_favorite fields to contacts

Revision ID: b29c94099e75
Revises: d4c55631d217
Create Date: 2025-03-15 02:53:26.782510

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b29c94099e75'
down_revision = 'd4c55631d217'
branch_labels = None
depends_on = None


def upgrade():
    # Add columns as nullable first
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('favorite', sa.Boolean(), nullable=True))
    
    # Update existing rows with default values
    op.execute("UPDATE contacts SET status = 'active', favorite = false")
    
    # Now make the columns non-nullable
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.alter_column('status', nullable=False)
        batch_op.alter_column('favorite', nullable=False)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.drop_column('favorite')
        batch_op.drop_column('status')
    # ### end Alembic commands ###