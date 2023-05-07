from . import db
from .secondary import items_shows, tags_shows

class Show(db.Model):
    __tablename__ = "shows"
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    description = db.Column(db.String())
    social_base_url = db.Column(db.String())
    contact_address = db.Column(db.String())
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
    items = db.relationship(
        "Item",
        secondary=items_shows,
        backref=db.backref("shows"),
        order_by="Item.play_date.desc()",
        lazy="dynamic",
        # TODO why is this not working? see item.shows assignment in api/item
        cascade_backrefs=False,
    )
    tags = db.relationship(
        "Tag",
        secondary=tags_shows,
        backref=db.backref("shows"),
        lazy="dynamic",
    )

    def __repr__(self):
        return "<Show #{}>".format(self.name)
