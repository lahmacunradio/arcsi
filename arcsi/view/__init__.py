from requests.api import request as rq

from flask import Blueprint


def form_api_request(method, endpoint):
    return rq(
        method,
        "http://web:5666" + endpoint,
        headers=headers,
        cookies={"session": request.cookies["session"]},
    )


router = Blueprint("router", __name__)


from .archive import *
from .data import *
from .forms import *
from .item import *
from .media import *
from .show import *
from .tag import *
from .user import *
