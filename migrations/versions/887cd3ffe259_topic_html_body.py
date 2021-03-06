"""topic html body

Revision ID: 887cd3ffe259
Revises: 17ea8104f107
Create Date: 2017-07-04 22:28:00.870140

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '887cd3ffe259'
down_revision = '17ea8104f107'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topics', sa.Column('body_html', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('topics', 'body_html')
    # ### end Alembic commands ###
