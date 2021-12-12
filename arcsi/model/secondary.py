from . import db

items_shows = db.Table(
    "items_shows",
    db.Column("show_id", db.Integer(), db.ForeignKey("shows.id")),
    db.Column("item_id", db.Integer(), db.ForeignKey("items.id")),
)

tags_items = db.Table(
    "tags_items",
    db.Column("item_id", db.Integer(), db.ForeignKey("items.id")),
    db.Column("tag_id", db.Integer(), db.ForeignKey("tags.id")),
)

tags_shows = db.Table(
    "tags_shows",
    db.Column("show_id", db.Integer(), db.ForeignKey("shows.id")),
    db.Column("tag_id", db.Integer(), db.ForeignKey("tags.id")),
)

shows_users = db.Table(
    "shows_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("users.id")),
    db.Column("show_id", db.Integer(), db.ForeignKey("shows.id")),
)

roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("users.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("roles.id")),
)
