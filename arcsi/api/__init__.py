from flask import Blueprint

arcsi = Blueprint("arcsi", __name__, url_prefix="/arcsi")

from .item import *
from .role import *
from .show import *
from .tag import *
from .user import *
from .data import *
from .media import media

arcsi.register_blueprint(media)

# TODO add routing here eg
# arcsi.route("/archive", methods=["GET"])(<method_name>)
