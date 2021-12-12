from . import db
from .secondary import tags_items

class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String())
    language = db.Column(db.String(5), default="hu_hu")
    play_date = db.Column(db.Date, nullable=False)
    image_url = db.Column(db.String())
    play_file_name = db.Column(db.String())
    length = db.Column(db.Integer)
    live = db.Column(db.Boolean, default=False)
    broadcast = db.Column(db.Boolean, default=False)
    airing = db.Column(db.Boolean, default=False)
    archive_lahmastore = db.Column(db.Boolean)
    archive_lahmastore_canonical_url = db.Column(db.String())
    archive_mixcloud = db.Column(db.Boolean)
    archive_mixcloud_canonical_url = db.Column(db.String())
    archived = db.Column(db.Boolean, default=False)
    download_count = db.Column(db.Integer)
    uploader = db.Column(db.String(), default="arcsi", nullable=False)
    uploaded_at = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )
    tags = db.relationship(
        "Tag",
        secondary=tags_items,
        backref=db.backref("items"),
        lazy="dynamic",
    )

    def __repr__(self):
        return "<Episode #{} -- {} -- {}>".format(
            self.number, self.play_date, self.name
        )
