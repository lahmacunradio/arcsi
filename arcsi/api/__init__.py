from flask import Blueprint

arcsi = Blueprint("arcsi", __name__, url_prefix="/arcsi")

from .archive import *
from .item import *
