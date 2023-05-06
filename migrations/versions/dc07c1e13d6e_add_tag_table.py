"""add Tag table

Revision ID: dc07c1e13d6e
Revises: 15d3ff65d9b2
Create Date: 2021-12-13 15:20:37.000031

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dc07c1e13d6e'
down_revision = '15d3ff65d9b2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tags',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('display_name', sa.String(length=66), nullable=False),
    sa.Column('clean_name', sa.String(length=66), nullable=False),
    sa.Column('icon', sa.String(), nullable=True),
    sa.Column('uploader', sa.String(), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('display_name')
    )
    op.create_table('tags_items',
    sa.Column('item_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['item_id'], ['items.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], )
    )
    op.create_table('tags_shows',
    sa.Column('show_id', sa.Integer(), nullable=True),
    sa.Column('tag_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['show_id'], ['shows.id'], ),
    sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tags_shows')
    op.drop_table('tags_items')
    op.drop_table('tags')
    # ### end Alembic commands ###
