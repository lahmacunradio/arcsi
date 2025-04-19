import requests

from datetime import datetime, timedelta

from flask import jsonify, make_response, request, redirect
from flask import current_app as app
from flask_security import auth_token_required, roles_accepted
from marshmallow import fields, post_load, Schema
from sqlalchemy import func

from uuid import uuid4

from . import arcsi
from .utils import archive, broadcast_audio, normalise, save_file
from .utils import form_filename, get_items, show_item_duplications_number
from arcsi.handler.upload import DoArchive
from arcsi.model import db
from arcsi.model.item import Item
from arcsi.model.show import Show
from arcsi.model.tag import Tag
from arcsi.model.utils import get_or_create


class ItemDetailsSchema(Schema):
    id = fields.Int()
    number = fields.Int(
        required=True
    )  # TODO value can't be 0 -- reserved for show itself
    name = fields.Str(required=True, min=1)
    name_slug = fields.Str(dump_only=True)
    description = fields.Str()
    language = fields.Str(max=5)
    play_date = fields.Date(
        required=False, load_default=datetime.today() + timedelta(days=1)
    )  # Thanks Kamil Szot!
    image_url = fields.Str(dump_only=True)
    play_file_name = fields.Str(dump_only=True)
    live = fields.Boolean()
    broadcast = fields.Boolean()
    # airing = fields.Boolean()
    archive_lahmastore = fields.Boolean(load_default=True)
    archive_lahmastore_canonical_url = fields.Str(dump_only=True)
    external_url = fields.Str()
    archived = fields.Boolean(dump_only=True)
    download_count = fields.Int(dump_only=True)
    uploader = fields.Str(required=True)
    shows = fields.List(
        fields.Nested(
            "ShowDetailsSchema",
            only=("id", "name", "archive_lahmastore_base_url"),
        ),
        required=True,
    )
    tags = fields.List(
        fields.Nested(
            "TagDetailsSchema",
            only=("id", "display_name", "clean_name"),
        )
    )

    @post_load
    def make_item(self, data, **kwargs):
        return Item(**data)


item_schema = ItemDetailsSchema()
item_archive_schema = ItemDetailsSchema(
    only=(
        "id",
        "number",
        "name",
        "name_slug",
        "description",
        "language",
        "play_date",
        "image_url",
        "play_file_name",
        "archived",
        "download_count",
        "shows",
        "tags",
    )
)
item_partial_schema = ItemDetailsSchema(
    partial=True,
)
items_schema = ItemDetailsSchema(many=True)
items_archive_schema = ItemDetailsSchema(
    many=True,
    only=(
        "id",
        "number",
        "name",
        "name_slug",
        "description",
        "language",
        "play_date",
        "image_url",
        "play_file_name",
        "archived",
        "download_count",
        "shows",
        "tags",
    ),
)
archon_items_schema = ItemDetailsSchema(
    many=True,
    only=("id", "number", "name", "play_date", "play_file_name", "archived", "shows"),
)

headers = {"Content-Type": "application/json"}


@arcsi.route("/item", methods=["GET"])
@arcsi.route("/archon/item/all", methods=["GET"])
@roles_accepted("admin", "host")
def archon_list_items():
    return archon_items_schema.dump(get_items())


@arcsi.route("/item/latest", methods=["GET"])
@auth_token_required
def frontend_list_items_latest():
    do = DoArchive()
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 12, type=int)
    items = (
        Item.query.filter(Item.play_date < datetime.today() - timedelta(days=1))
        .filter(Item.archived == True)
        .order_by(Item.play_date.desc(), Item.id.desc())
        .paginate(page=page, per_page=size, error_out=False)
    )
    for item in items.items:
        if item.image_url:
            item.image_url = do.download(
                item.shows[0].archive_lahmastore_base_url, item.image_url
            )
        item.name_slug = normalise(item.name)
    return items_archive_schema.dump(items.items)


# As a legacy it's still used by the frontend in a fallback mechanism,
# It should be replaced with the /show/<string:show_slug>/item/<string:item_slug>
@arcsi.route("/item/<int:id>", methods=["GET"])
@roles_accepted("admin", "host", "guest")
def archon_view_item(id):
    item_query = Item.query.filter_by(id=id)
    item = item_query.first_or_404()
    if item:
        if item.image_url:
            do = DoArchive()
            item.image_url = do.download(
                item.shows[0].archive_lahmastore_base_url, item.image_url
            )
        item.name_slug = normalise(item.name)
        return item_schema.dump(item)
    else:
        return make_response("Item not found", 404, headers)


@arcsi.route("/archon/item/add", methods=["POST"])
@roles_accepted("admin", "host")
def archon_add_item():
    no_error = True
    error = ""
    if request.is_json:
        return make_response(
            jsonify("Only accepts multipart/form-data for now, sorry"), 503, headers
        )
    # work around ImmutableDict type
    item_metadata = request.form.to_dict()
    # TODO if we could send JSON payloads w/ ajax then this prevalidation isn't needed
    item_metadata["shows"] = [
        {"id": item_metadata["shows"], "name": item_metadata["show_name"]}
    ]
    item_metadata["tags"] = [
        {"display_name": tag_name.strip()}
        for tag_name in item_metadata["taglist"].split(",")
    ]
    item_metadata["tags"] = [
        dict(t) for t in {tuple(d.items()) for d in item_metadata["tags"]}
    ]
    item_metadata.pop("show_name", None)
    item_metadata.pop("taglist", None)
    item_metadata.pop("airing", None)

    # validate payload
    err = item_schema.validate(item_metadata)
    if err:
        return make_response(
            jsonify(
                "Fix your form. Invalid data sent to add item, see: {}".format(err)
            ),
            500,
            headers,
        )
    else:
        item_metadata = item_schema.load(item_metadata)
        download_count = 0
        length = 0
        archived = False
        image_file_name = None
        image_file = None
        image_url = ""
        play_file = None
        play_file_name = None
        default_archive_lahmastore = True
        archive_lahmastore_canonical_url = ""
        external_url = ""
        shows = (
            db.session.query(Show)
            .filter(Show.id.in_((show.id for show in item_metadata.shows)))
            .all()
        )
        tags = (
            get_or_create(
                Tag,
                display_name=tag.display_name,
                clean_name=normalise(tag.display_name),
            )
            for tag in item_metadata.tags
        )
        new_item = Item(
            number=item_metadata.number,
            name=item_metadata.name,
            description=item_metadata.description,
            external_url=item_metadata.external_url,
            language=item_metadata.language,
            play_date=item_metadata.play_date,
            image_url=image_url,
            play_file_name=play_file_name,
            length=length,
            # Value represents whether an episode airs as a live broadcast
            live=item_metadata.live,
            # TODO Clarify broadcast meaning currently the value is used during file upload, signals the intent of upload request. If true, the client wants to air the upload.
            # After cleanup it would maybe represent recording as a broadcast type
            broadcast=item_metadata.broadcast,
            # Value represents if the request wants to upload to storage too
            archive_lahmastore=default_archive_lahmastore,
            # Stores the result of the archive intent (above). Returns a Url or None
            archive_lahmastore_canonical_url=archive_lahmastore_canonical_url,
            # Internal property is set when audio has finished uploading to storage. Represents the result of a broadcast intent, true or false.
            # After cleanup it could keep this role to make it simple to handle live episode audio to archives.
            archived=archived,
            download_count=download_count,
            uploader=item_metadata.uploader,
            shows=shows,
            tags=tags,
        )

        # Check for duplicate files
        name_occurrence = show_item_duplications_number(new_item)

        db.session.add(new_item)
        db.session.flush()

        # TODO get show cover img and set as fallback
        if request.files:
            # Defend against possible duplicate files
            if 0 < name_occurrence:
                version_prefix = uuid4()
                item_name = "{}-{}".format(new_item.name, version_prefix)
            else:
                item_name = new_item.name

            # process files first
            if request.files.get("play_file"):
                if request.files["play_file"] != "":
                    play_file = request.files["play_file"]

                    new_item.play_file_name = save_file(
                        archive_base=new_item.shows[0].archive_lahmastore_base_url,
                        archive_idx=new_item.number,
                        archive_file=play_file,
                        archive_file_name=(new_item.shows[0].name, item_name),
                    )

            if request.files.get("image_file"):
                if request.files["image_file"] != "":
                    image_file = request.files["image_file"]

                    image_file_name = save_file(
                        archive_base=new_item.shows[0].archive_lahmastore_base_url,
                        archive_idx=new_item.number,
                        archive_file=image_file,
                        archive_file_name=(new_item.shows[0].name, item_name),
                    )

            if new_item.broadcast:
                # we require both image and audio if broadcast (Azuracast) is set
                if not (image_file_name and new_item.play_file_name):
                    no_error = False
                    error = "ERROR: Both image and audio input are required if broadcast is set"
                    app.logger.debug(error)
            # this branch is typically used for pre-uploading live episodes (no audio)
            else:
                if not image_file_name:
                    no_error = False
                    error = "ERROR: You need to add at least an image"
                    app.logger.debug(error)

        # archive files if asked
        if new_item.archive_lahmastore:
            if no_error and (play_file or image_file):
                if image_file_name:
                    new_item.image_url = archive(
                        archive_base=new_item.shows[0].archive_lahmastore_base_url,
                        archive_file_name=image_file_name,
                        archive_idx=new_item.number,
                    )
                    if not new_item.image_url:
                        no_error = False
                        error = "ERROR: Image could not be uploaded to storage"
                        app.logger.debug(error)

                if new_item.play_file_name:
                    new_item.archive_lahmastore_canonical_url = archive(
                        archive_base=new_item.shows[0].archive_lahmastore_base_url,
                        archive_file_name=new_item.play_file_name,
                        archive_idx=new_item.number,
                    )

                    if new_item.archive_lahmastore_canonical_url:
                        # Only set archived if there is audio data otherwise it's live episode
                        new_item.archived = True
                    else:  # Upload didn't succeed
                        no_error = False
                        error = "ERROR: Audio could not be uploaded to storage"
                        app.logger.debug(error)

        # broadcast episode if asked
        if new_item.broadcast and no_error:
            if not (play_file and image_file):
                no_error = False
                error = (
                    "ERROR: Both image and audio input are required if broadcast is set"
                )
                app.logger.debug(error)
            else:
                new_item.airing = broadcast_audio(
                    archive_base=new_item.shows[0].archive_lahmastore_base_url,
                    archive_idx=new_item.number,
                    broadcast_file_name=new_item.play_file_name,
                    broadcast_playlist=new_item.shows[0].playlist_name,
                    broadcast_show=new_item.shows[0].name,
                    broadcast_title=new_item.name,
                    image_file_name=image_file_name,
                )
                if not new_item.airing:
                    no_error = False
                    error = "ERROR: Item could not be uploaded to the broadcast station"
                    app.logger.debug(error)

            # TODO some mp3 error
            # TODO Maybe I used vanilla mp3 not from azuracast
            # item_audio_obj = MP3(item_path)
            # return item_audio_obj.filename
            # item_length = item_audio_obj.info.length

        db.session.commit()
        # TODO no_error is just bandaid for proper exc handling
        if no_error:
            return make_response(
                jsonify(item_schema.dump(new_item)),
                200,
                headers,
            )
        return make_response(
            jsonify(
                {
                    "error": {
                        "message": "Some error happened, check server logs for details. Note that your media may have been uploaded (to DO and/or Azurcast).",
                        "errorReason": error,
                        "code": 10205070,
                    }
                },
                500,
                headers,
            )
        )


# It's still used by the application for sure, and maybe by the frontend (?)
@arcsi.route("/item/<int:id>/listen", methods=["GET"])
@roles_accepted("admin", "host")
def listen_play_file(id):
    do = DoArchive()
    item_query = Item.query.filter_by(id=id)
    item = item_query.first()
    presigned = do.download(
        item.shows[0].archive_lahmastore_base_url, item.archive_lahmastore_canonical_url
    )
    return presigned


# Not used anywhere
@arcsi.route("/archon/item/<int:id>/download", methods=["GET"])
@roles_accepted("admin", "host")
def archon_download_play_file(id):
    do = DoArchive()
    item_query = Item.query.filter_by(id=id)
    item = item_query.first_or_404()
    presigned = do.download(
        item.shows[0].archive_lahmastore_base_url, item.archive_lahmastore_canonical_url
    )
    return redirect(presigned, code=302)


# TODO implement delete functionality
@arcsi.route("/archon/item/<int:id>", methods=["DELETE"])
@roles_accepted("admin", "host")
def archon_delete_item(id):
    item_query = Item.query.filter_by(id=id)
    item = item_query.first_or_404()
    item_query.delete()
    db.session.commit()
    return make_response("Deleted item successfully", 200, headers)


@arcsi.route("/archon/item/<int:id>/edit", methods=["POST"])
@roles_accepted("admin", "host")
def archon_edit_item(id):
    do = DoArchive()
    no_error = True
    error = ""
    image_file = None
    image_file_name = None
    play_file = None

    item_query = Item.query.filter_by(id=id)
    item = item_query.first_or_404()

    # work around ImmutableDict type
    item_metadata = request.form.to_dict()

    # TODO if we could send JSON payloads w/ ajax then this prevalidation isn't needed
    item_metadata["shows"] = [
        {"id": item_metadata["shows"], "name": item_metadata["show_name"]}
    ]
    item_metadata["tags"] = [
        {"display_name": tag_name.strip()}
        for tag_name in item_metadata["taglist"].split(",")
    ]
    item_metadata["tags"] = [
        dict(t) for t in {tuple(d.items()) for d in item_metadata["tags"]}
    ]
    item_metadata.pop("taglist", None)
    item_metadata.pop("show_name", None)

    # validate payload
    # TODO handle what happens on f.e: empty payload?
    # if err: -- need to check files {put IMG, put AUDIO} first
    err = item_schema.validate(item_metadata)
    if err:
        return make_response(
            jsonify("Invalid data sent to edit item, see: {}".format(err)),
            500,
            headers,
        )
    else:
        # TODO edit uploaded media -- remove re-up etc.
        # TODO broadcast / airing
        item_metadata = item_schema.load(item_metadata)

        # Check for duplicate files (before item is updated!)
        name_occurrence = show_item_duplications_number(item_metadata)

        item.number = item_metadata.number
        item.name = item_metadata.name
        item.description = item_metadata.description
        item.language = item_metadata.language
        item.play_date = item_metadata.play_date
        item.live = item_metadata.live
        item.broadcast = item_metadata.broadcast
        item.airing = item_metadata.airing
        item.uploader = item_metadata.uploader
        item.archive_lahmastore = item_metadata.archive_lahmastore
        item.external_url = item_metadata.external_url

        # conflict between shows from detached object load(item_metadata) added to session vs original persistent object item from query
        item.shows = (
            db.session.query(Show)
            .filter(Show.id.in_((show.id for show in item_metadata.shows)))
            .all()
        )
        item.tags = (
            get_or_create(
                Tag,
                display_name=tag.display_name,
                clean_name=normalise(tag.display_name),
            )
            for tag in item_metadata.tags
        )
        # TODO Implement upsert https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert
        db.session.add(item)
        db.session.flush()
        empty_files = all([not (_v) for _v in request.files.values()])
        request_files = {k: v for k, v in request.files.items()}

        # Defend against possible duplicate files
        if 0 < name_occurrence:
            version_prefix = uuid4()
            item_name = "{}-{}".format(item.name, version_prefix)
        else:
            item_name = item.name
        # TODO Update after py update, python3.10+ supports patmat
        if empty_files and (not (item.broadcast and item.archive_lahmastore)):
            db.session.commit()
            return make_response(jsonify(item_partial_schema.dump(item)), 200, headers)
        elif empty_files and (item.archive_lahmastore and (not item.broadcast)):
            return make_response(
                jsonify(
                    {
                        "error": {
                            "message": "To edit an episode's archives select attachments and ensure they have acceptable extensions (eg. mp3, jpg, jpeg, png, gif). You need to at least add an image or turn off the `archive` checkmark.",
                            "errorReason": "ERROR: Image handler returned empty",
                            "code": 10201010,
                        }
                    },
                    400,
                    headers,
                )
            )
        elif (
            (empty_files or (not request_files["play_file"]))
            and (item.broadcast and (not item.archive_lahmastore))
            and (not item.archived)
        ):
            return make_response(
                jsonify(
                    {
                        "error": {
                            "message": "To broadcast an edited episode an audio file is needed. This episode has no audio archived. (This is the initial state of live episodes). No audio file was provided. Please attach an audio.",
                            "errorReason": "ERROR: Audio handler returned empty",
                            "code": 10205030,
                        }
                    },
                    400,
                    headers,
                )
            )

        if item.archive_lahmastore:
            save_errors = {}

            for name, file in request_files.items():
                if not file:
                    continue
                if name == "play_file":
                    item.play_file_name = save_file(
                        archive_base=item.shows[0].archive_lahmastore_base_url,
                        archive_idx=item.number,
                        archive_file=file,
                        archive_file_name=(item.shows[0].name, item_name),
                    )
                    if item.play_file_name:
                        item.archive_lahmastore_canonical_url = archive(
                            archive_base=item.shows[0].archive_lahmastore_base_url,
                            archive_file_name=item.play_file_name,
                            archive_idx=item.number,
                        )
                        # Only set archived if there is audio data otherwise it's live episode
                        if item.archive_lahmastore_canonical_url:
                            item.archived = True
                        else:
                            app.logger.debug(item)
                            save_errors.update({name: {"type": "nwdo"}})
                    else:
                        app.logger.debug(request_files)
                        save_errors.update({name: {"type": "fs"}})

                elif name == "image_file":
                    image_file_name = save_file(
                        archive_base=item.shows[0].archive_lahmastore_base_url,
                        archive_idx=item.number,
                        archive_file=file,
                        archive_file_name=(item.shows[0].name, item_name),
                    )
                    if image_file_name:
                        item.image_url = archive(
                            archive_base=item.shows[0].archive_lahmastore_base_url,
                            archive_file_name=image_file_name,
                            archive_idx=item.number,
                        )

                        if not item.image_url:
                            app.logger.debug(item)
                            save_errors.update({name: {"type": "nwdo"}})
                    else:
                        app.logger.debug(item_name, image_file_name)
                        save_errors.update({name: {"type": "fs"}})

            if save_errors:
                return make_response(
                    jsonify(
                        {
                            "error": {
                                "message": "Failed to upload file(s) to Lahmastore. Try again later or contact an administrator.",
                                "errorReason": "ERROR: {}".format(save_errors.items()),
                                "code": 10202030,
                            }
                        },
                        400,
                        headers,
                    )
                )
            else:
                db.session.commit()

        if item.broadcast:
            image_url_name = None
            play_url_name = None
            temp_urls = []
            if request_files["play_file"] and request_files.get("play_file"):
                # TODO Save only when file doesnt exist
                app.logger.info(item.name, item_name, item_metadata)
                if item.play_file_name != form_filename(
                    request_files["play_file"], (item.shows[0].name, item_name)
                ):
                    play_url_name = save_file(
                        archive_base=item.shows[0].archive_lahmastore_base_url,
                        archive_idx=item.number,
                        archive_file=request_files["play_file"],
                        archive_file_name=(item.shows[0].name, item_name),
                    )
                    if not play_url_name:
                        temp_urls.append(False)
                else:
                    play_url_name = item.play_file_name
            else:
                (tmp_file_saved, play_url_name) = do.tmp_save_file(
                    item.shows[0].archive_lahmastore_base_url,
                    item.archive_lahmastore_canonical_url,
                    item.number,
                )
                temp_urls.append(tmp_file_saved)
            if request_files["image_file"] and request_files.get("image_file"):
                if not item.image_url:
                    image_url_name = save_file(
                        archive_base=item.shows[0].archive_lahmastore_base_url,
                        archive_idx=item.number,
                        archive_file=request_files["image_file"],
                        archive_file_name=(item.shows[0].name, item_name),
                    )
                    if not image_url_name:
                        temp_urls.append(False)
                else:
                    image_url_name = item.image_url.rsplit("/", 1)[1]
            else:
                if item.shows[0].cover_image_url:
                    fallback_image = item.shows[0].cover_image_url
                else:
                    fallback_image = "/static/img/lahmacun-logo.png"

                (tmp_image_saved, image_url_name) = do.tmp_save_file(
                    item.shows[0].archive_lahmastore_base_url,
                    fallback_image,
                    0,
                )
                temp_urls.append(tmp_image_saved)
            if temp_urls:
                for saved in temp_urls:
                    if not saved:
                        return make_response(
                            jsonify(
                                {
                                    "error": {
                                        "message": "Episode not found in storage. The system provided the following error.",
                                        "errorReason": "ERROR: Request to {} returned {}: {},".format(
                                            presigned, resp.status_code, resp.reason
                                        ),
                                        "code": 10201030,
                                    }
                                },
                                404,
                                headers,
                            )
                        )

            item.airing = broadcast_audio(
                archive_base=item.shows[0].archive_lahmastore_base_url,
                archive_idx=item.number,
                broadcast_file_name=play_url_name,
                broadcast_playlist=item.shows[0].playlist_name,
                broadcast_show=item.shows[0].name,
                broadcast_title=item.name,
                image_file_name=image_url_name,
            )

            if item.airing:
                db.session.commit()
            # TODO cleanup tmp files after upload?
            # Rollback automatically happens when the api request context closes (ie. at return statements).
            else:
                return make_response(
                    jsonify(
                        {
                            "error": {
                                "message": "Upload to broadcast station failed. The system provided the following error. Try if an older episode or a smaller file can be uploaded. Contact your administrator and try again later.",
                                "errorReason": "ERROR: Request to radio station raised an exception.",
                                "code": 10208090,
                            }
                        },
                        400,
                        headers,
                    )
                )
        return make_response(jsonify(item_partial_schema.dump(item)), 200, headers)

        if request.files:
            # Defend against possible duplicate files
            if 0 < name_occurrence:
                version_prefix = uuid4()
                item_name = "{}-{}".format(item.name, version_prefix)
            else:
                item_name = item.name

            # process files first
            if request.files["image_file"]:
                if request.files["image_file"] != "":
                    image_file = request.files["image_file"]

                    image_file_name = save_file(
                        archive_base=item.shows[0].archive_lahmastore_base_url,
                        archive_idx=item.number,
                        archive_file=image_file,
                        archive_file_name=(item.shows[0].name, item_name),
                    )

            if request.files["play_file"]:
                if request.files["play_file"] != "":
                    play_file = request.files["play_file"]

                    item.play_file_name = save_file(
                        archive_base=item.shows[0].archive_lahmastore_base_url,
                        archive_idx=item.number,
                        archive_file=play_file,
                        archive_file_name=(item.shows[0].name, item_name),
                    )
            if item.broadcast:
                # we require both image and audio if broadcast (Azuracast) is set
                if not (image_file_name and item.play_file_name):
                    no_error = False
                    error = "ERROR: Both image and audio input are required if broadcast (Azuracast) is set"
                    app.logger.debug(error)
                # this branch is typically used for pre-uploading live episodes (no audio)
                else:
                    if not image_file_name:
                        no_error = False
                        error = "ERROR: You need to add at least an image"
                        app.logger.debug(error)

            # archive files if asked
            if item.archive_lahmastore:
                if no_error and (play_file or image_file):
                    if image_file_name:
                        item.image_url = archive(
                            archive_base=item.shows[0].archive_lahmastore_base_url,
                            archive_file_name=image_file_name,
                            archive_idx=item.number,
                        )
                        if not item.image_url:
                            no_error = False
                            error = "ERROR: Image could not be uploaded to storage"
                            app.logger.debug(error)

                    if item.play_file_name:
                        item.archive_lahmastore_canonical_url = archive(
                            archive_base=item.shows[0].archive_lahmastore_base_url,
                            archive_file_name=item.play_file_name,
                            archive_idx=item.number,
                        )
                        # Only set archived if there is audio data otherwise it's live episode
                        if item.archive_lahmastore_canonical_url:
                            item.archived = True
                        else:
                            no_error = False
                            error = "ERROR: Audio could not be uploaded to storage"
                            app.logger.debug(error)

            # broadcast episode if asked
            if item.broadcast and no_error:
                if not (play_file and image_file):
                    no_error = False
                    error = "ERROR: Both image and audio input are required if broadcast (Azuracast) is set"
                    app.logger.debug(error)
                else:
                    item.airing = broadcast_audio(
                        archive_base=item.shows[0].archive_lahmastore_base_url,
                        archive_idx=item.number,
                        broadcast_file_name=item.play_file_name,
                        broadcast_playlist=item.shows[0].playlist_name,
                        broadcast_show=item.shows[0].name,
                        broadcast_title=item.name,
                        image_file_name=image_file_name,
                    )
                    if not item.airing:
                        no_error = False
                        error = "ERROR: Item could not be uploaded to Azuracast"
                        app.logger.debug(error)

            db.session.commit()
            if no_error:
                return make_response(
                    jsonify(item_partial_schema.dump(item)), 200, headers
                )
            return make_response(
                jsonify(
                    {
                        "error": {
                            "message": "Some error happened, check server logs for details. Note that your media may have been uploaded (to DO and/or Azurcast).",
                            "errorReason": error,
                            "code": 10205070,
                        }
                    },
                    500,
                    headers,
                )
            )


@arcsi.route("/item/search", methods=["GET"])
@auth_token_required
def frontend_search_item():
    do = DoArchive()
    page = request.args.get("page", 1, type=int)
    size = request.args.get("size", 12, type=int)
    param = request.args.get("param", "lahmacun", type=str)
    items = (
        Item.query.filter(
            func.lower(Item.name).contains(func.lower(param))
            | func.lower(Item.description).contains(func.lower(param))
        )
        .filter(Item.play_date < datetime.today() - timedelta(days=1))
        .order_by(Item.play_date.desc())
        .paginate(page=page, per_page=size, error_out=False)
    )
    for item in items.items:
        if item.image_url:
            item.image_url = do.download(
                item.shows[0].archive_lahmastore_base_url, item.image_url
            )
        item.name_slug = normalise(item.name)
    return items_schema.dumps(items.items)
