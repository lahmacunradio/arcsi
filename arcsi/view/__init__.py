from flask import Blueprint

router = Blueprint("router", __name__) 


from .add import *
from .archive import *