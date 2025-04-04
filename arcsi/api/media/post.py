from b64uuid import B64UUID
from datetime import datetime, timedelta

from flask import jsonify, make_response, request, redirect
from flask import current_app as app
from flask_security import auth_token_required, roles_accepted

from uuid import uuid4

from . import media, MediaSimpleSchema
from arcsi.api.utils import (
    archive,
    allowed_file,
    form_filename,
    normalise,
    raise_extension,
    save_file,
    get_items,
    show_item_duplications_number,
)
from arcsi.handler.file import size
from arcsi.handler.upload import DoArchive
from arcsi.model import db
from arcsi.model.media import Media

from arcsi.model.utils import get_or_create


schema = MediaSimpleSchema()

headers = {"Content-Type": "application/json"}
accept_headers = {
    "Accept-Post": "application/json; charset=UTF-8",
    "Content-Type": "application/json",
}

"""
Order of processing
-- http request = fast error
-- request
      -- file,
      -- data
         = validation
-- file into data
-- db
"""


@media.route("/new", methods=["POST"])
def insert_media():
    if request.is_json:
        return make_response(
            jsonify("Request must be multipart/form-data"), 415, accept_headers
        )
    if not request.files:
        return make_response(
            jsonify("Request must contain at least one file"), 400, headers
        )

    valids = {}
    for fname, f in request.files.items():
        if not allowed_file(f.filename):
            return make_response(
                jsonify(
                    "Request files must be of {}".format(
                        app.config["ALLOWED_EXTENSIONS"]
                    )
                ),
                400,
                headers,
            )
        if not f.content_length < 8192:  # TODO add app.config("fs-limit")n
            return make_response(
                jsonify(
                    "File size is too large. Limited to 8192. Actual {}".format(
                        f.content_length
                    ),
                    400,
                    headers,
                )
            )

        valids.update(
            {
                f.name: {
                    "size": f.content_length,
                    "_content_type": f.content_type,
                    "_name": f.filename,  # TODO normalise
                    "ext": raise_extension(f.filename),
                }
            }
        )
        ## extract size and guard here -- check whether Content-Size is total or per-file
        ## then we check if allowed file type -- depending on above final order might change
    app.logger.info("VALIDS\t{}".format(valids))

    if not valids.items():
        app.logger.info("app found valid files to upload")
        return make_response(
            jsonify(
                "All upload attempts have been rejected. No valid upload file found"
            ),
            400,
            headers,
        )

    media_metadata = request.form.to_dict()
    media_metadata["external_storage"] = bool(media_metadata["external_storage"])

    err = schema.validate(media_metadata)
    if err:
        return make_response(
            jsonify("Invalid data sent to add media: {}".format(err)), 500, headers
        )
    # Successfully validated both meta and file
    else:
        for _naming, valid in valids.items():
            # Serialise, create new object
            media_metadata["size"] = valid["size"]  # TODO use conjoin map
            media_metadata["extension"] = valid["ext"]

            new_media = schema.load(media_metadata)
            ### TODO For size to be calculated we need a valid local_name
            #        new_media["size"] = size(local_name)

            #
            new_media.name = "{}-{}".format(
                new_media.name, B64UUID(new_media.id).string
            )

            # TODO Make future file handler check that archive path is valid eg. url or localpath
            # TODO Allow external urls also (hogy mukodne media cache retegunk kulso adattal?
            # Maintain backward compatibility of URL formats
            if media_metadata.get("binding"):
                bind_path = media_metadata["binding"].split("_")
                # Create URL with unique suffix for all new media
                formed_url = archive(bind_path[0], new_media["name"], bind_path[1])
                bind = media_metadata["binding"]
            else:
                bind = None
                formed_url = None
            new_media.binding = bind
            new_media.url = formed_url

            new_media.dimension = 0
            # TODO Refactor fun raise show.items from it
            # if show_item_duplications_number(new_media):
            #    new_media["name"] = _form_hashed_name(local_name, uuid)
            # TODO use formed name for "name" field

            # Persist to storage
            db.session.add(new_media)
            db.session.flush()
            db.session.commit()

            return schema.dump(new_media)


## Helper funcs
def _make_uuid():
    return str(uuid4())


def _form_hashed_name(file_name, hashing):
    return "{}-{}".format(file_name, hashing)
