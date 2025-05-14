from . import db


class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(), unique=True, nullable=False)
    clean_name = db.Column(db.String(), nullable=False)
    icon = db.Column(db.String())
    uploader = db.Column(db.String(), default="arcsi", nullable=False)
    uploaded_at = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )

    def __repr__(self):
        return "<Tag #{} -- {}>".format(self.display_name, self.uploader)
