from flask_security import RoleMixin

from . import db


class Role(db.Model, RoleMixin):
    """
    Proposed roles:
    * admin -- everything
    * host -- manage show, manage items
    * guest -- manage item(s)
    """

    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), unique=True, nullable=False)
    description = db.Column(db.String())

    def __repr__(self):
        return "<Role {}>".format(self.name)

    @property
    def present_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
        }
