"""username_normalized_and_updated_at

Revision ID: d110e9b808da
Revises: b2a3fed378d5
Create Date: 2018-03-03 14:50:45.653085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd110e9b808da'
down_revision = 'b2a3fed378d5'
branch_labels = None
depends_on = None
set_username_normalized_sql = """
UPDATE users SET username_normalized = lower(username)
"""
set_updated_at = """
UPDATE users SET updated_at = created_at
"""


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('username_normalized', sa.String(length=32), nullable=True))
    op.create_index(op.f('ix_users_username_normalized'), 'users', ['username_normalized'], unique=True)
    op.drop_index('ix_users_username', table_name='users')
    # ### end Alembic commands ###
    op.execute(set_username_normalized_sql)
    op.execute(set_updated_at)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.drop_index(op.f('ix_users_username_normalized'), table_name='users')
    op.drop_column('users', 'username_normalized')
    op.drop_column('users', 'updated_at')
    # ### end Alembic commands ###