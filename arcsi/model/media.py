from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID

from . import db


class Media(db.Model):
    __tablename__ = "medias"
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = db.Column(db.String(), nullable=False)
    extension = db.Column(db.String(), nullable=False)
    # URL is constructed from name, id, ext
    url = db.Column(db.String(256))
    size = db.Column(db.Integer, nullable=False)
    external_storage = db.Column(db.Boolean, nullable=False)
    # Storage process if needed part 1.3
    storage_process = db.Column(db.Integer, nullable=False, default=0)
    # For picture dimension is XxY | For audio dimension is length
    dimension = db.Column(db.String())
    # Show or episode
    tie = db.Column(db.String(), nullable=True)
    # Formed name of related show/episode/etc.
    binding = db.Column(db.String(), nullable=True)
    # source = FK sec tables (part 1.2)
    created_at = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )
    # Use this field for registering queue sccess -- TODO part 1.4
    uploaded_at = db.Column(db.DateTime)

    def __repr__(self):
        return "<Media {}>".format(str(self.id))
