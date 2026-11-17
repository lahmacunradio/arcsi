from flask import Blueprint
from flask import current_app as app
from flask_caching import Cache

arcsi = Blueprint("arcsi", __name__, url_prefix="/arcsi")
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})

from .item import *
from .role import *
from .show import *
from .tag import *
from .user import *
from .data import *

# TODO add routing here eg
# arcsi.route("/archive", methods=["GET"])(<method_name>)
