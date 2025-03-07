"""Fix UUID issue

Revision ID: d4c55631d217
Revises: 
Create Date: 2025-03-06 07:20:51.052571

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4c55631d217'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.drop_index('idx_contacts_user_id')
        batch_op.create_index(batch_op.f('ix_contacts_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_contacts_user_id'), ['user_id'], unique=False)
        batch_op.drop_constraint('fk_user', type_='foreignkey')
        batch_op.create_foreign_key(None, 'users', ['user_id'], ['id'])

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('oauth_provider', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('oauth_id', sa.String(length=255), nullable=True))
        batch_op.alter_column('password_hash',
               existing_type=sa.TEXT(),
               type_=sa.String(length=255),
               nullable=True)
        batch_op.drop_index('idx_users_email')
        batch_op.drop_constraint('users_email_key', type_='unique')
        batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_users_id'), ['id'], unique=False)
        batch_op.create_unique_constraint(None, ['oauth_id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_index(batch_op.f('ix_users_id'))
        batch_op.drop_index(batch_op.f('ix_users_email'))
        batch_op.create_unique_constraint('users_email_key', ['email'])
        batch_op.create_index('idx_users_email', ['email'], unique=False)
        batch_op.alter_column('password_hash',
               existing_type=sa.String(length=255),
               type_=sa.TEXT(),
               nullable=False)
        batch_op.drop_column('oauth_id')
        batch_op.drop_column('oauth_provider')

    with op.batch_alter_table('contacts', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('fk_user', 'users', ['user_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_index(batch_op.f('ix_contacts_user_id'))
        batch_op.drop_index(batch_op.f('ix_contacts_id'))
        batch_op.create_index('idx_contacts_user_id', ['user_id'], unique=False)

    # ### end Alembic commands ###
