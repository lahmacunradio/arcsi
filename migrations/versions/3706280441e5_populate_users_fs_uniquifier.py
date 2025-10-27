"""populate_users_fs_uniquifier

Revision ID: 3706280441e5
Revises: 6fa7d5c511aa
Create Date: 2025-09-11 23:52:26.316993

"""

import hashlib
import os
import sqlalchemy as sa

from alembic import op

from arcsi.model.user import User

# revision identifiers, used by Alembic.
revision = "3706280441e5"
down_revision = "6fa7d5c511aa"
branch_labels = None
depends_on = None


# Assume column is already added
def upgrade():
    conn = op.get_bind()
    users = conn.execute(sa.select(User.id, User.fs_uniquifier)).fetchall()
    for user in users:
        unique_hash = hashlib.md5(os.urandom(32)).hexdigest()
        conn.execute(
            sa.update(User).where(User.id == user.id),
            [{"fs_uniquifier": unique_hash}],
        )

    op.alter_column("users", "fs_uniquifier", nullable=False)
    op.create_unique_constraint("user_fs_uniquifier_key", "users", ["fs_uniquifier"])


def downgrade():
    conn = op.get_bind()
    users = conn.execute(sa.select(User)).fetchall()
    op.alter_column("users", "fs_uniquifier", nullable=True)
    op.drop_constraint("user_fs_uniquifier_key", "users", type_="unique")
    for user in users:
        conn.execute(
            sa.update(User).where(User.id == user.id),
            [{"fs_uniquifier": None}],
        )
