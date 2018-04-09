"""body_html_for_message

Revision ID: f33ffc0ea91d
Revises: 1e59d6c8c940
Create Date: 2018-04-09 13:57:39.801046

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f33ffc0ea91d'
down_revision = '1e59d6c8c940'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('messages', sa.Column('body_html', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('messages', 'body_html')
    # ### end Alembic commands ###
