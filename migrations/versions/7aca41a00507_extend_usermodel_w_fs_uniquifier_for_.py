"""Extend UserModel w fs_uniquifier for Flask-Secu 4+

Revision ID: 7aca41a00507
Revises: 610e758af79c
Create Date: 2025-09-01 22:45:49.434966

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7aca41a00507"
down_revision = "610e758af79c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("fs_uniquifier", sa.String(length=64), nullable=True, unique=True),
    )


def downgrade():
    op.drop_column("user", "fs_uniquifier")
