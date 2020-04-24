from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Item(db.Model):
    __tablename__ = "items"
    # TODO null and non-null constraints etc
    id = db.Column(db.Integer, primary_key=True)
    show_name = db.Column(db.String())
    # TODO COVER ART FOR SHOW // EPISODE ? Blob object? URL?
    show_cover_url = db.Column(db.String())
    episode_number = db.Column(db.Integer)
    episode_title = db.Column(db.String())
    episode_length = db.Column(db.Integer)  # millis? time?
    episode_cover_url = db.Column(db.String())
    episode_date = db.Column(db.String())  # date?
    # TODO BLOB OBJECT FULL SOURCE?
    source_url = db.Column(db.String())
    archive_url = db.Column(db.String())
    # result_all = db.Column(JSON)

    def __init__(
        self,
        show_name,
        show_cover_url,
        ep_num,
        ep_title,
        episode_length,
        episode_cover_url,
        episode_date,
        source_url,
        archive_url,
    ):
        self.show_name = show_name
        self.show_cover_url = show_cover_url
        self.episode_number = ep_num
        self.episode_title = ep_title
        self.episode_length = episode_length
        self.episode_cover_url = episode_cover_url
        self.episode_date = episode_date
        self.source_url = source_url
        self.archive_url = archive_url

    def __repr__(self):
        return "<Item #{}>".format(self.id)

    @property
    def present_dict(self):
        return {
            "id": self.id,
            "show_name": self.show_name,
            "show_cover_url": self.show_cover_url,
            "episode_number": self.episode_number,
            "episode_title": self.episode_title,
            "episode_length": self.episode_length,
            "episode_cover_url": self.episode_cover_url,
            "episode_date": self.episode_date,
            "source_url": self.source_url,
            "archive_url": self.archive_url,
        }
