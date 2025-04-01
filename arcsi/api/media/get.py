from datetime import datetime, timedelta

from flask import jsonify, make_response, request, redirect
from flask import current_app as app
from flask_security import auth_token_required, roles_accepted

from sqlalchemy import func

from uuid import uuid4

from . import media, MediaSimpleSchema
from arcsi.api.utils import archive, broadcast_audio, normalise, save_file
from arcsi.api.utils import get_items, show_item_duplications_number
from arcsi.handler.upload import DoArchive
from arcsi.model import db
from arcsi.model.media import Media

from arcsi.model.utils import get_or_create


schema = MediaSimpleSchema(
    many=True, only=("id", "url", "dimension", "size", "created_at")
)

headers = {"Content-Type": "application/json"}


@media.route("/all", methods=["GET"])
@media.route("", methods=["GET"])  # root of blueprint see media/__init__.py
def select_all():
    return schema.dump(Media.query.all())
