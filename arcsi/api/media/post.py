from b64uuid import B64UUID
from datetime import datetime, timedelta
from uuid import uuid4

from flask import jsonify, make_response, request, redirect
from flask import current_app as app
from flask_security import auth_token_required, roles_accepted
from werkzeug.utils import secure_filename


from . import media, MediaSimpleSchema
from arcsi.api.utils import (
    archive,
    allowed_file,
    get_items,
    save_file,
    show_item_duplications_number,
)
from arcsi.handler.file import get_extension, tidy_name, path, local_save
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


@media.route("/<int:id>", methods=["POST"])
def update_media(id):
    if not request.content_type.startswith("multipart/form-data"):
        return make_response(
            jsonify("Request must be multipart/form-data"), 415, accept_headers
        )
    if request.files:
        return make_response(jsonify("Request must not contain files"), 400, headers)


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
        secured_filename = secure_filename(f.filename)
        if not allowed_file(secured_filename):
            return make_response(
                jsonify(
                    "Request files must be of {}".format(
                        app.config["ALLOWED_EXTENSIONS"]
                    )
                ),
                400,
                headers,
            )
        if secured_filename == "":
            return make_response(
                jsonify("Request file is missing name"),
                400,
                headers,
            )

        if f.content_length:
            app.logger.info("Receive file size -- request header includes length")
            file_length = round(f.content_length / 1024, 1)
        else:
            app.logger.info("Calculate file size -- request header missing length")
            try:
                file_length = round(len(f.read()) / 1024, 1)
            except:
                return make_response(
                    jsonify("Throwing file -- could not be read", 400, headers)
                )
            finally:
                f.seek(0, 0)

        if not file_length < 8192:  # TODO add app.config("MAX_CONTENT_LENGTH")?
            return make_response(
                jsonify(
                    "File size is too large. Limited to 8192 Kb. Actual {} Kb".format(
                        file_length
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

    app.logger.info("VALIDS\t{}".format(valids))

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
    media_metadata["external_storage"] = bool(media_metadata["external_storage"])

    for _naming, valid in valids.items():
        # Serialise, create new object
        media_metadata["id"] = B64UUID(_make_uuid()).string
        media_metadata["size"] = valid["size"]  # TODO use conjoin all mapping
        media_metadata["extension"] = valid["ext"]

        # TODO Make future file handler check that archive path is valid eg. url or localpath
        # TODO Allow external urls also (hogy mukodne media cache retegunk kulso adattal?
        # Maintain backward compatibility of URL formats
        if media_metadata.get("binding"):
            binds = media_metadata.get("binding").split("_")
            space = binds[0]
            idx = binds[1]
            media_metadata["name"] = "{}".format(binds[2])
        else:
            space = media_metadata["id"]
            idx = media_metadata["id"]

        # Create URL with unique suffix for all new media
        media_metadata["name"] = "{}-{}".format(
            media_metadata["name"], media_metadata["id"]
        )

        file_name = tidy_name(valid["ext"], space, media_metadata["name"])
        file_path = path(space, idx, file_name)

        if not media_metadata["external_storage"]:
            # media_metadata["url"] = archive(space, file_name, idx)
            media_metadata["url"] = _archive(file_path, space, idx)
        else:
            media_metadata["url"] = "http://localhost/{}".format(
                # save_file(space, idx, valid["file"], file_name)
                _save_file(file_path, valid["file"]).split("/", 1)[1]
            )

        media_metadata["dimension"] = str(0)

        app.logger.info("{}".format(media_metadata["url"]))
        app.logger.info(
            "{} --> {}".format(media_metadata["id"], B64UUID(media_metadata["id"]).uuid)
        )
        app.logger.info(
            "{} <-- {}".format(
                str(B64UUID(media_metadata["id"]).uuid), media_metadata["id"]
            )
        )
        err = schema.validate(media_metadata)
        if err:
            return make_response(
                jsonify("Invalid data sent to add media: {}".format(err)), 500, headers
            )
        # Successfully validated both meta and file
        # -- upload file
        # -- load new item
        # -- persist to db
        else:

            new_media = schema.load(media_metadata)

            ### TODO For size to be calculated we need a valid local_name
            #        new_media["size"] = size(local_name)

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
def _archive(path, space, idx):
    do = DoArchive()
    archive_file_path = path

    archive_url = do.upload(
        archive_file_path,  # TODO change this to either path or request.file
        space,
        idx,
    )
    return archive_url


def _save_file(path, file):
    app.logger.info("MEDIA/STATUS/SAVE FILE: path: {}".format(path))
    app.logger.info("MEDIA/STATUS/SAVE FILE: archive_file: {}".format(file))
    return local_save(file, path)


def _make_uuid():
    return str(uuid4())


def _form_hashed_name(file_name, hashing):
    return "{}-{}".format(file_name, hashing)
