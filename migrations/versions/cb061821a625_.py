"""empty message

Revision ID: cb061821a625
Revises: 42f2db168fb2
Create Date: 2020-07-02 01:07:33.442941

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cb061821a625'
down_revision = '42f2db168fb2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('items', sa.Column('airing', sa.Boolean(), nullable=True))
    op.add_column('items', sa.Column('language', sa.String(length=5), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('items', 'language')
    op.drop_column('items', 'airing')
    # ### end Alembic commands ###