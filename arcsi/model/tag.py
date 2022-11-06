from . import db


class Tag(db.Model):
    __tablename__ = "tags"
    id = db.Column(db.Integer, primary_key=True)
    display_name = db.Column(db.String(66), nullable=False, unique=True)
    clean_name = db.Column(db.String(66), nullable=False)
    icon = db.Column(db.String())
    created_at = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )


    def __repr__(self):
        return "<Tag {}>".format(
            self.clean_name
        )
