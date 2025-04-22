from requests.api import request as rq

from flask import Blueprint


router = Blueprint("router", __name__)


from .archive import *
from .data import *
from .forms import *
from .item import *
from .media import *
from .show import *
from .tag import *
from .user import *
