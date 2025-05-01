import requests

from datetime import datetime, timedelta

from flask import jsonify, make_response, request, redirect
from flask import current_app as app
from flask_security import auth_token_required, roles_accepted

from sqlalchemy import func

from uuid import uuid4

from . import media, MediaSimpleSchema
from arcsi.api.utils import archive, broadcast_audio, normalise, save_file
from arcsi.api.utils import get_filtered_query, get_items, show_item_duplications_number
from arcsi.handler.upload import DoArchive
from arcsi.model.media import Media


headers = {"Content-Type": "application/json"}

schema = MediaSimpleSchema(
    only=(
        "id",
        "url",
        "dimension",
        "size",
        "tie",
        "binding",
        "name",
        "extension",
    ),
)


@media.route("/all", methods=["GET"])
@media.route("/list", methods=["GET"])
@media.route("", methods=["GET"])  # root of this blueprint see media/__init__.py
def all():
    return schema.dump(Media.query.all(), many=True)


@media.route("/<id>", methods=["GET"])
def one(id):
    partial_media = schema.load(
        {"id": id}, partial=True
    )  # load() triggers after_load() which returns media object with transformed id

    if partial_media.id:
        one = get_filtered_query(
            Media, partial_media.id
        ).scalar_one()  # transformed id is used to make query
        app.logger.info(one.name)
        serial_media = schema.dump(one)
        app.logger.info(serial_media)
        return serial_media
    else:
        return make_response(jsonify("Media not found"), 404, headers)
