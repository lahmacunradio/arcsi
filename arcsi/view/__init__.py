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


headers = {"Content-Type": "application/json"}


# Optional keyword arguments: model id, api endpoint, http method
# Default method: GET
def request_api(model, **kwargs):
    request_method = "GET" if not kwargs.get("method") else kwargs.pop("method")
    endpoint = ["http://web:5666", model]
    if kwargs.get("id"):
        endpoint = endpoint.append(kwargs["id"])
    if kwargs.get("endpoint"):
        endpoint = endpoint.append(kwargs["endpoint"]
    request_endpoint = "/".join(endpoint)
    return rq(request_method, request_endpoint, {headers: headers})
