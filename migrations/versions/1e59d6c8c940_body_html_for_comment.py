"""body_html_for_comment

Revision ID: 1e59d6c8c940
Revises: 9cc084b1c4eb
Create Date: 2018-04-06 19:03:13.956543

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1e59d6c8c940'
down_revision = '9cc084b1c4eb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comments', sa.Column('body_html', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('comments', 'body_html')
    # ### end Alembic commands ###
