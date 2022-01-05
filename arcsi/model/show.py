from .secondary import items_shows
from . import db


class Show(db.Model):
    __tablename__ = "shows"
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    description = db.Column(db.String())
    language = db.Column(db.String(5), default="hu_hu")
    # TODO rename to image_url
    cover_image_url = db.Column(db.String())
    playlist_name = db.Column(db.String())
    frequency = db.Column(db.Integer, nullable=False, default=1)
    week = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    start = db.Column(db.Time, nullable=False)
    end = db.Column(db.Time, nullable=False)
    archive_lahmastore = db.Column(db.Boolean, default=True)
    archive_lahmastore_base_url = db.Column(db.String())
    archive_mixcloud = db.Column(db.Boolean, default=False)
    archive_mixcloud_base_url = db.Column(db.String())
    items = db.relationship(
        "Item",
        secondary=items_shows,
        backref=db.backref("shows"),
        lazy="dynamic",
        order_by="desc(Item.play_date)",
        # TODO why is this not working? see item.shows assignment in api/item
        cascade_backrefs=False,
    )
    # categories eg noice-jazz-core-salsa

    def __repr__(self):
        return "<Show #{}>".format(self.name)
