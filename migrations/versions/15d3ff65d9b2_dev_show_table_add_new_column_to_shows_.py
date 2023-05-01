"""dev(Show table): Add new column to Shows table: External link / social media Url

Revision ID: 15d3ff65d9b2
Revises: f02d05e78a7a
Create Date: 2023-01-29 18:37:53.892177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '15d3ff65d9b2'
down_revision = 'f02d05e78a7a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('shows', sa.Column('social_base_url', sa.String(length=108), nullable=True))
    op.drop_column('shows', 'archive_mixcloud_base_url')
    op.drop_column('shows', 'archive_mixcloud')
    op.add_column('items', sa.Column('social_base_url', sa.String(length=108), nullable=True))
    op.drop_column('items', 'archive_mixcloud_canonical_url')
    op.drop_column('items', 'archive_mixcloud')

def downgrade():
    op.add_column('shows', sa.Column('archive_mixcloud', sa.Boolean(), nullable=True))
    op.add_column('shows', sa.Column('archive_mixcloud_base_url', sa.String(), nullable=True))
    op.drop_column('shows', 'social_base_url')
    op.add_column('items', sa.Column('archive_mixcloud', sa.Boolean(), nullable=True))
    op.add_column('items', sa.Column('archive_mixcloud_canonical_url', sa.String(), nullable=True))
    op.drop_column('items', 'social_base_url')
