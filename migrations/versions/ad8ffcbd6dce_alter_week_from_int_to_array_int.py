"""alter week from int to array<int>

Revision ID: ad8ffcbd6dce
Revises: 7aca41a00507
Create Date: 2026-09-09 21:26:33.439510

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

# revision identifiers, used by Alembic.
revision = "ad8ffcbd6dce"
down_revision = "7aca41a00507"
branch_labels = None
depends_on = None


def upgrade():
    # create temporary week_array column
    op.add_column("shows", sa.Column("week_array", sa.ARRAY(sa.Integer)))
    shows = table(
        "shows", column("week", sa.Integer), column("week_array", sa.ARRAY(sa.Integer))
    )
    # fill out week_array according to week values
    op.execute(
        shows.update()
        .where(shows.c.week == 1)
        .values({"week_array": op.inline_literal("{0, 1, 2, 3}")})
    )
    op.execute(
        shows.update()
        .where(shows.c.week == 0)
        .values({"week_array": op.inline_literal("{4}")})
    )
    # replace week with week_array
    op.drop_column("shows", "week")
    op.alter_column("shows", "week_array", nullable=False, new_column_name="week")


def downgrade():
    # create temporary week_temp
    op.add_column("shows", sa.Column("week_temp", sa.Integer))
    shows = table(
        "shows", column("week", sa.ARRAY(sa.Integer)), column("week_temp", sa.Integer)
    )
    # fill out week_temp according to week values
    op.execute(
        shows.update()
        .where(shows.c.week == {0, 1, 2, 3})
        .values({"week_temp": op.inline_literal(1)})
    )
    op.execute(
        shows.update()
        .where(shows.c.week == {4})
        .values({"week_temp": op.inline_literal(0)})
    )
    # drop week and replace it with week_temp
    op.drop_column("shows", "week")
    op.alter_column("shows", "week_temp", nullable=False, new_column_name="week")
