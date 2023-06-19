"""increase_max_size_of_external_url

Revision ID: 610e758af79c
Revises: ea81f5721b70
Create Date: 2023-06-14 09:53:04.998815

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '610e758af79c'
down_revision = 'ea81f5721b70'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('items', 'social_base_url', existing_type=sa.String(length=108), type_=sa.String(length=256), new_column_name='external_url')
    op.alter_column('shows', 'social_base_url', existing_type=sa.String(length=108), type_=sa.String(length=256), new_column_name='external_url')


def downgrade():
    op.alter_column('items', 'external_url', existing_type=sa.String(length=256), type_=sa.String(length=108), new_column_name='social_base_url')
    op.alter_column('shows', 'external_url', existing_type=sa.String(length=256), type_=sa.String(length=108), new_column_name='social_base_url')
