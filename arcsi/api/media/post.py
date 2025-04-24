from b64uuid import B64UUID
from datetime import datetime, timedelta
import requests
from uuid import uuid4

from flask import jsonify, make_response, request, redirect
from flask import current_app as app
from flask_security import auth_token_required, roles_accepted
from werkzeug.utils import secure_filename


from . import media, MediaSimpleSchema
from arcsi.api.utils import (
    archive,
    allowed_file,
    get_filtered_query,
    get_items,
    save_file,
    show_item_duplications_number,
)
from arcsi.handler.file import (
    get_extension,
    get_audio_length,
    get_image_dimension,
    tidy_name,
    path,
    local_save,
    is_image,
    is_audio,
)
from arcsi.handler.upload import DoArchive
from arcsi.model import db
from arcsi.model.media import Media

from arcsi.model.utils import get_or_create


schema = MediaSimpleSchema()

headers = {"Content-Type": "application/json"}
accept_headers = {
    "Accept-Post": "multipart/form-data; charset=UTF-8",
    "Content-Type": "application/json",
}


@media.route("/<id>", methods=["POST"])
def update(id):
    if not request.content_type.startswith("multipart/form-data"):
        return make_response(
            jsonify("Request must be multipart/form-data"), 415, accept_headers
        )
    if request.files:
        return make_response(jsonify("Request must not contain files"), 400, headers)


    media_metadata = request.form.to_dict()
    media_metadata["id"] = id
    err = schema.validate(media_metadata)
    if err:
        return make_response(
            jsonify("Invalid formed data sent to add media: {}".format(err)),
            500,
            headers,
        )
    else:
        # Convert between id formats
         edited = schema.load(media_metadata)
         original = get_filtered_query(Media, edited.id).scalar_one()
         # Make hashed name for the edited media name
         if original.name != edited.name:
             edited.name =  tidy_name(
                original.extension,
                id,
                _form_hashed_name(edited.name, id),
            )

        if tie:
            # TODO
            pass


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
"""
Endpoint responsible for handling files of the request.
It implements logic to create new rows in the Media table
It has 2 main parts: writing files to storage (local- or external-storage), writing to the db
Covers 2 user flows. 1, new free media 2, new bound media by show or episode relations.
"""


@media.route("/new", methods=["POST"])
def insert():
    if not request.content_type.startswith("multipart/form-data"):
        return make_response(
            jsonify("Request must be multipart/form-data"), 415, accept_headers
        )
    if not request.files:
        return make_response(
            jsonify("Request must contain at least one file"), 400, headers
        )

    valids = {}
    for fname, f in request.files.items():
        if not f:
            continue  ## File upload form is empty (no file was selected by the user)
        secured_filename = secure_filename(f.filename)
        if not allowed_file(secured_filename):
            return make_response(
                jsonify(
                    "Request files must be of {} (received {})".format(
                        app.config["ALLOWED_EXTENSIONS"], secured_filename
                    )
                ),
                400,
                headers,
            )
        if secured_filename == "":
            return make_response(
                jsonify("Request file is missing"),
                400,
                headers,
            )

        if f.content_length:
            app.logger.debug("Receive file size -- request header includes length")
            file_length = round(f.content_length / 1024, 1)
        else:
            app.logger.debug("Calculate file size -- request header missing length")
            try:
                file_length = round(len(f.read()) / 1024, 1)
            except:
                return make_response(
                    jsonify("Throwing file -- could not be read", 400, headers)
                )
            finally:
                f.seek(0, 0)

        if not file_length < (20 * 8192) and is_audio(get_extension(secured_filename)):
            return make_response(
                jsonify(
                    "File size is too large. Limited to 160 Mb. Actual {} Mb".format(
                        file_length
                    ),
                    400,
                    headers,
                )
            )
        elif not file_length < 8192 and is_image(get_extension(secured_filename)):
            return make_response(
                jsonify(
                    "File {} size is too large. Limited to 8192 Kb. Actual {} Kb".format(
                        f.filename, file_length
                    ),
                    400,
                    headers,
                )
            )

        valids.update(
            {
                f.name: {
                    "size": file_length,
                    "name": secured_filename,
                    "ext": get_extension(secured_filename),
                    "file": f,
                }
            }
        )

    if not valids.items():
        return make_response(
            jsonify(
                "All upload attempts have been rejected. No valid upload file found"
            ),
            400,
            headers,
        )
    # Keep clean copy for all valid items
    media_metadata = request.form.to_dict()

    for _naming, valid in valids.items():
        # create new object properties
        media_metadata["id"] = B64UUID(_make_uuid()).string
        media_metadata["size"] = valid["size"]
        media_metadata["extension"] = valid["ext"]

        # TODO Allow external urls also (depends on cloudflare media cache)
        # Maintain backward compatibility of URL formats
        # TODO schema has tie and binding too -- maybe tie is going to be about the intent
        if media_metadata.get("binding"):
            [space, idx, media_metadata["name"]] = media_metadata.get("binding").split(
                "_"
            )
        else:
            space = media_metadata["name"]
            idx = media_metadata["id"]

        err = schema.validate(media_metadata)
        if err:
            return make_response(
                jsonify("Invalid formed data sent to add media: {}".format(err)),
                500,
                headers,
            )
        # Successfully validated both meta and file
        else:
            # Serialise for a second time to edit before calling schema.load()
            media_metadata = schema.dump(media_metadata)
            # Create URL with unique suffix for all new media
            file_name = tidy_name(
                valid["ext"],
                space,
                _form_hashed_name(media_metadata["name"], media_metadata["id"]),
            )

            if media_metadata.get("external_storage"):
                media_metadata["url"] = _archive(file_name, space, idx)
            else:
                media_metadata["external_storage"] = False
                media_metadata["url"] = "http://localhost/{}".format(
                    _save_file(space, idx, valid["file"], file_name).split("/", 1)[1]
                )

            if is_image(valid["ext"]):
                media_metadata["dimension"] = get_image_dimension(valid["file"])
            elif is_audio(valid["ext"]):
                media_metadata["dimension"] = get_audio_length(valid["file"])
            else:
                media_metadata["dimension"] = "0x0"

            # Persist to storage
            new_media = schema.load(media_metadata)
            db.session.add(new_media)
            db.session.flush()
            db.session.commit()

            return schema.dump(new_media)


## Helper funcs


def _archive(name, space, idx):
    do = DoArchive()
    archive_file_path = path(space, idx, name)

    archive_url = do.upload(
        archive_file_path,  # TODO change this from path to streaming request.file chunks
        space,
        idx,
    )
    return archive_url


def _save_file(space, idx, file, name):
    save_file_path = path(space, idx, name)
    return local_save(file, save_file_path)


def _make_uuid():
    return str(uuid4())


def _form_hashed_name(file_name, hashing):
    return "{}-{}".format(file_name, hashing)
