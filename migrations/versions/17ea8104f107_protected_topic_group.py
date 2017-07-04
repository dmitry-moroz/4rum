"""protected topic group

Revision ID: 17ea8104f107
Revises: 60a695d8d2e3
Create Date: 2017-07-04 15:20:35.001189

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '17ea8104f107'
down_revision = '60a695d8d2e3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('topic_groups', sa.Column('protected', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('topic_groups', 'protected')
    # ### end Alembic commands ###
