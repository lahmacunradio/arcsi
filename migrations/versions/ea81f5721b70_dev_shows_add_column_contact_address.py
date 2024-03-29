"""dev(shows): add column contact_address

Revision ID: ea81f5721b70
Revises: dc07c1e13d6e
Create Date: 2023-01-29 21:48:23.533614

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ea81f5721b70'
down_revision = 'dc07c1e13d6e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('shows', sa.Column('contact_address', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('shows', 'contact_address')
    # ### end Alembic commands ###
