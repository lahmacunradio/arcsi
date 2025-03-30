from datetime import datetime, timedelta

from flask import jsonify, make_response, request, redirect
from flask import current_app as app
from flask_security import auth_token_required, roles_accepted

from uuid import uuid4

from . import media, MediaSimpleSchema
from arcsi.api.utils import archive, broadcast_audio, normalise, save_file
from arcsi.api.utils import get_items, show_item_duplications_number
from arcsi.handler.upload import DoArchive
from arcsi.model import db
from arcsi.model.media import Media

from arcsi.model.utils import get_or_create


schema = MediaSimpleSchema()

headers = {"Content-Type": "application/json"}


@media.route("/new", methods=["POST"])
def insert_media():
    if request.is_json:
        return make_response(jsonify("Only accepts multipart/form-data"), 503, headers)
    media_metadata = request.form.to_dict()
    media_metadata["name"] = "bonbon"
    media_metadata["extension"] = "jpg"
    media_metadata["external_storage"] = bool(media_metadata["external_storage"])
    media_metadata["size"] = 0
    local_name = "{}.{}".format(media_metadata["name"], media_metadata["extension"])
    err = schema.validate(media_metadata)
    if err:
        return make_response(
            jsonify("Invalid data sent to add media: {}".format(err)), 500, headers
        )
    # Successfully validated meta and file
    else:
        uuid = _make_uuid()
        app.logger.info(uuid)
        media_metadata["id"] = uuid
        # TODO Refactor fun raise show.items from it
        # if show_item_duplications_number(media_metadata):
        #    media_metadata["name"] = _form_hashed_name(local_name, uuid)
        # TODO use formed name for "name" field

        new_media = schema.make_media(media_metadata)
        app.logger.info(new_media)
        db.session.add(new_media)
        db.session.flush()
        db.session.commit()
        app.logger.info(Media.query.all())
        return schema.dump(new_media)


def _make_uuid():
    return uuid4()


def _form_hashed_name(file_name, hashing):
    return "{}-{}".format(file_name, hashing)
