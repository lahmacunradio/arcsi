from flask import Blueprint

router = Blueprint("router", __name__)

from .forms import *
from .archive import *
from .item import *
from .show import *
from .user import *
from .data import *