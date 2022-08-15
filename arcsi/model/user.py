from flask_security import UserMixin

from . import db
from .secondary import roles_users, shows_users


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    active = db.Column(db.Boolean, default=True)
    butt_user = db.Column(db.String())
    butt_pw = db.Column(db.String(128))
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users"), lazy="dynamic"
    )
    shows = db.relationship(
        "Show",
        secondary=shows_users,
        backref=db.backref("users"),
        lazy="dynamic",
        # TODO will this work ?
        cascade_backrefs=False,
    )

    def __repr__(self):
        return "<Host {}>".format(self.name)
