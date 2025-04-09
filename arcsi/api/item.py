import requests

from datetime import datetime, timedelta

from flask import jsonify, make_response, request, redirect
from flask_security import auth_token_required, roles_accepted
from marshmallow import fields, post_load, Schema
from marshmallow.validate import Length
from sqlalchemy import func

from . import arcsi
from .utils import (
    process_files,
    archive_files,
    broadcast_episode,
    cleanup_show_playlist,
    cleanup_tmp_files,
    normalise,
    get_items,
    show_item_duplications_number,
)
from arcsi.handler.upload import DoArchive
from arcsi.model import db
from arcsi.model.item import Item
from arcsi.model.show import Show
from arcsi.model.tag import Tag
from arcsi.model.utils import get_or_create


class ItemDetailsSchema(Schema):
    id = fields.Int()
    number = fields.Int(required=True)
    # TODO value can't be 0 -- reserved for show itself
    name = fields.Str(required=True, validate=Length(min=1))
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
    error = False
    error_message = ""
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
        image_url = ""
        play_file_name = None
        default_archive_lahmastore = True
        archive_lahmastore_canonical_url = ""
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
            # overwrites item's play_file_name and broadcast
            new_item, image_file_name, error, error_message = process_files(
                request,
                new_item,
                name_occurrence,
                image_file_name,
                error,
                error_message,
            )

        # cleanup previous episode from show's playlist
        if new_item.live and (error == False):
            cleanup_show_playlist(new_item.shows[0].playlist_name)

        # archive files if asked
        if new_item.archive_lahmastore:
            # overwrites item's image_url, archive_lahmastore_canonical_url and archived
            new_item, error, error_message = archive_files(
                new_item, image_file_name, error, error_message
            )

        # broadcast episode if asked
        if new_item.broadcast and (error == False):
            # overwrites item's airing
            new_item, error, error_message = broadcast_episode(
                new_item, image_file_name, error, error_message
            )

        db.session.commit()
        # TODO error is just bandaid for proper exc handling
        if error == False:
            cleanup_tmp_files(new_item)
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
                        "errorReason": error_message,
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
    error = False
    error_message = ""
    image_file_name = None

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

        db.session.add(item)
        db.session.flush()

        app.logger.debug(request.files.items())
        app.logger.debug(request.files.lists())
        app.logger.debug(request.files.listvalues())

        empty_files = all([not (_v) for _v in request.files.values()])

        if empty_files:
            if item.broadcast and item.archived:
                presigned_play = do.download(
                    item.shows[0].archive_lahmastore_base_url,
                    item.archive_lahmastore_canonical_url,
                )
                presigned_image = do.download(
                    item.shows[0].archive_lahmastore_base_url,
                    item.image_url,
                )
                temp_urls = [
                    (item.play_file_name, presigned_play),
                    (item.image_url.rsplit("/")[0], presigned_image),
                ]
                for temp_name, presigned in temp_urls:
                    resp = requests.get(presigned, stream=True)
                    if resp.ok:
                        with open(
                            media_path(
                                item.shows[0].archive_lahmastore_base_url,
                                str(item.number),
                                temp_name,
                            ),
                            "wb",
                        ) as _temp_file:
                            for chunk in resp.iter_content(chunk_size=4 * 1024):
                                _temp_file.write(chunk)
                    else:
                        return make_response(
                            jsonify(
                                {
                                    "error": {
                                        "message": "Episode not found in storage. The system provided the following error.",
                                        "errorReason": error,
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
                        broadcast_file_name=item.play_file_name,
                        broadcast_playlist=item.shows[0].playlist_name,
                        broadcast_show=item.shows[0].name,
                        broadcast_title=item.name,
                        image_file_name=image_file_name,
                    )

                if item.airing:
                    db.session.commit()
                    return make_response(
                        jsonify(item_partial_schema.dump(item)), 200, headers
                    )
                # TODO cleanup tmp files after upload
                # TODO rollback for db -- needed?
                else:
                    return make_response(
                        jsonify(
                            {
                                "error": {
                                    "message": "Upload to broadcast station failed. The system provided the following error. Try if an older episode or a smaller file can be uploaded. Contact your administrators.",
                                    "errorReason": error,
                                    "code": 10208090,
                                }
                            },
                            400,
                            headers,
                        )
                    )

            db.session.commit()
            return make_response(jsonify(item_partial_schema.dump(item)), 200, headers)

        if request.files:
            # overwrites item's play_file_name and broadcast
            item, image_file_name, error, error_message = process_files(
                request,
                item,
                name_occurrence,
                image_file_name,
                error,
                error_message,
            )

        # cleanup previous episode from show's playlist
        if item.live and (error == False):
            cleanup_show_playlist(item.shows[0].playlist_name)

        # archive files if asked
        if item.archive_lahmastore:
            # overwrites item's image_url, archive_lahmastore_canonical_url and archived
            item, error, error_message = archive_files(
                item, image_file_name, error, error_message
            )

        # broadcast episode if asked
        if item.broadcast and (error == False):
            # overwrites item's airing
            item, error, error_message = broadcast_episode(
                item, image_file_name, error, error_message
            )

        db.session.commit()
        if error == False:
            if request.files:
                cleanup_tmp_files(item)
            return make_response(jsonify(item_partial_schema.dump(item)), 200, headers)
        return make_response(
            jsonify(
                {
                    "error": {
                        "message": "Some error happened, check server logs for details. Note that your media may have been uploaded (to DO and/or Azurcast).",
                        "errorReason": error_message,
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
    return items_schema.dump(items.items)
