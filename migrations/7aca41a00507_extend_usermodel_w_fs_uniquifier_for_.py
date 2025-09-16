"""Extend UserModel w fs_uniquifier for Flask-Secu 4+

Revision ID: 7aca41a00507
Revises: 610e758af79c
Create Date: 2025-09-01 22:45:49.434966

"""

from alembic import op
import sqlalchemy as sa
import uuid


# revision identifiers, used by Alembic.
revision = "7aca41a00507"
down_revision = "610e758af79c"
branch_labels = None
depends_on = None

# https://flask-security-too.readthedocs.io/en/stable/changelog.html#id51


def upgrade():
    # be sure to MODIFY this line to make nullable=True:
    op.add_column(
        "users",
        sa.Column("fs_uniquifier", sa.String(length=64), nullable=True),
    )

    # update existing rows with unique fs_uniquifier
    user_table = sa.Table(
        "users",
        sa.MetaData(),
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("fs_uniquifier", sa.String),
    )
    conn = op.get_bind()
    for row in conn.execute(sa.select([user_table.c.id])):
        conn.execute(
            user_table.update()
            .values(fs_uniquifier=uuid.uuid4().hex)
            .where(user_table.c.id == row["id"])
        )

    # finally - set nullable to false
    op.alter_column("users", "fs_uniquifier", nullable=False)


def downgrade():
    op.drop_column("users", "fs_uniquifier")
