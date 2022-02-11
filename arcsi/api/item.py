import json
import os
import requests
import io

from mutagen.id3 import APIC, ID3
from mutagen.mp3 import MP3

from flask import flash, jsonify, make_response, request, send_file, url_for, redirect
from flask import current_app as app
from marshmallow import fields, post_load, Schema, ValidationError

from uuid import uuid4

from .utils import (
    archive,
    broadcast_audio,
    dict_to_obj,
    media_path,
    save_file,
)
from arcsi.api import arcsi
from arcsi.handler.upload import DoArchive
from arcsi.model import db
from arcsi.model.item import Item
from arcsi.model.show import Show


class ItemDetailsSchema(Schema):
    id = fields.Int()
    number = fields.Int(
        required=True
    )  # TODO value can't be 0 -- reserved for show itself
    name = fields.Str(required=True, min=1)
    description = fields.Str()
    language = fields.Str(max=5)
    play_date = fields.Date(required=True)
    image_url = fields.Str(dump_only=True)
    play_file_name = fields.Str(dump_only=True)
    live = fields.Boolean()
    broadcast = fields.Boolean()
    airing = fields.Boolean(dump_only=True)
    archive_lahmastore = fields.Boolean()
    archive_lahmastore_canonical_url = fields.Str(dump_only=True)
    archive_mixcloud = fields.Boolean()
    archive_mixcloud_canonical_url = fields.Str(dump_only=True)
    archived = fields.Boolean(dump_only=True)
    download_count = fields.Int(dump_only=True)
    uploader = fields.Str(required=True)
    shows = fields.List(
        fields.Nested(
            "ShowDetailsSchema",
            only=("id", "name"),
        ),
        required=True,
    )

    @post_load
    def make_item(self, data, **kwargs):
        return Item(**data)


item_schema = ItemDetailsSchema()
item_archive_schema = ItemDetailsSchema(only = ("name", "number", "play_date", "language", 
                                             "description", "image_url", "play_file_name", "download_count"))
item_partial_schema = ItemDetailsSchema(partial=True,)
items_schema = ItemDetailsSchema(many=True)
items_archive_schema = ItemDetailsSchema(many=True, 
                                                   only=("name", "description",
                                                         "play_date", "play_file_name",
                                                         "image_url", "download_count"))

headers = {"Content-Type": "application/json"}


@arcsi.route("/item", methods=["GET"])
@arcsi.route("/item/all", methods=["GET"])
def list_items():
    do = DoArchive()
    items = Item.query.all()
    for item in items:
        if item.image_url:
            item.image_url = do.download(
                item.shows[0].archive_lahmastore_base_url, item.image_url
            )
    return items_schema.dumps(items)

@arcsi.route("/item/latest/", methods=["GET"])
def list_items_latest():
    do = DoArchive()
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 12, type=int)
    items = Item.query.order_by(Item.play_date.desc()).paginate(
        page, size, False)
    for item in items.items:
        if item.image_url:
            item.image_url = do.download(
                item.shows[0].archive_lahmastore_base_url, item.image_url
            )
    return items_archive_schema.dumps(items.items)


@arcsi.route("/item/<id>", methods=["GET"])
def view_item(id):
    item_query = Item.query.filter_by(id=id)
    item = item_query.first_or_404()
    if item:
        if item.image_url:
            do = DoArchive()
            item.image_url = do.download(
                item.shows[0].archive_lahmastore_base_url, item.image_url
            )
        return item_schema.dump(item)
    else:
        return make_response("Item not found", 404, headers)


@arcsi.route("/item", methods=["POST"])
def add_item():
    no_error = True
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
    item_metadata.pop("show_name", None)
    # validate payload
    err = item_schema.validate(item_metadata)
    if err:
        return make_response(
            jsonify("Invalid data sent to add item, see: {}".format(err)), 500, headers
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
        archive_lahmastore_canonical_url = ""
        archive_mixcloud_canonical_url = ""
        shows = (
            db.session.query(Show)
            .filter(Show.id.in_((show.id for show in item_metadata.shows)))
            .all()
        )

        new_item = Item(
            number=item_metadata.number,
            name=item_metadata.name,
            description=item_metadata.description,
            language=item_metadata.language,
            play_date=item_metadata.play_date,
            image_url=image_url,
            play_file_name=play_file_name,
            length=length,
            live=item_metadata.live,
            broadcast=item_metadata.broadcast,
            archive_lahmastore=item_metadata.archive_lahmastore,
            archive_lahmastore_canonical_url=archive_lahmastore_canonical_url,
            archive_mixcloud=item_metadata.archive_mixcloud,
            archive_mixcloud_canonical_url=archive_mixcloud_canonical_url,
            archived=archived,
            download_count=download_count,
            uploader=item_metadata.uploader,
            shows=shows,
        )

        name_occurrence = int(db.session.query(db.func.count()).filter(new_item.name == Item.name, new_item.number == Item.number).scalar())
        app.logger.debug("Name_occurence (duplicate detection before flush): {}".format(name_occurrence))

        db.session.add(new_item)
        db.session.flush()

        # TODO get show cover img and set as fallback
        if request.files:
            # Defend against possible duplicate files
            name_occurrence = int(db.session.query(db.func.count()).filter(new_item.name == Item.name, new_item.number == Item.number).scalar())
            app.logger.debug("Name_occurence (duplicate detection): {}".format(name_occurrence))

            if name_occurrence:
                version_prefix = uuid4()
                item_name = "{}-{}".format(version_prefix, new_item.name)
            else:
                item_name = new_item.name

            # process files first
            if request.files["play_file"]:
                if request.files["play_file"] != "":
                    play_file = request.files["play_file"]  

                    new_item.play_file_name = save_file(
                        archive_base=new_item.shows[0].archive_lahmastore_base_url,
                        archive_idx=new_item.number,
                        archive_file=play_file,
                        archive_file_name=(new_item.shows[0].name, item_name),
                    )

            if request.files["image_file"]:
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
            # this branch is typically used for pre-uploading live episodes (no audio)
            else: 
                if not image_file_name:
                    no_error = False

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

        # broadcast episode if asked
        if new_item.broadcast and no_error:
            if not (play_file and image_file):
                no_error = False
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
        else:
            return "Some error happened, check server logs for details. Note that your media may have been uploaded (to DO and/or Azurcast)."


@arcsi.route("item/<id>/listen", methods=["GET"])
def listen_play_file(id):
    do = DoArchive()
    item_query = Item.query.filter_by(id=id)
    item = item_query.first()
    presigned = do.download(
        item.shows[0].archive_lahmastore_base_url, item.archive_lahmastore_canonical_url
    )
    return presigned


@arcsi.route("/item/<id>/download", methods=["GET"])
def download_play_file(id):
    do = DoArchive()
    item_query = Item.query.filter_by(id=id)
    item = item_query.first_or_404()
    presigned = do.download(
        item.shows[0].archive_lahmastore_base_url, item.archive_lahmastore_canonical_url
    )
    return redirect(presigned, code=302)


@arcsi.route("/item/<id>", methods=["DELETE"])
def delete_item(id):
    item_query = Item.query.filter_by(id=id)
    item = item_query.first_or_404()
    item_query.delete()
    db.session.commit()
    return make_response("Deleted item successfully", 200, headers)


@arcsi.route("/item/<id>", methods=["POST"])
def edit_item(id):
    no_error = True
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
        item.archive_mixcloud = item_metadata.archive_mixcloud

        # conflict between shows from detached object load(item_metadata) added to session vs original persistent object item from query
        item.shows = (
            db.session.query(Show)
            .filter(Show.id.in_((show.id for show in item_metadata.shows)))
            .all()
        )
        
        name_occurrence = int(db.session.query(db.func.count()).filter(item.name == Item.name, item.number == Item.number).scalar())
        app.logger.debug("Name_occurence (duplicate detection before flush): {}".format(name_occurrence))
        
        db.session.add(item)
        db.session.flush()

        if request.files:
            # Defend against possible duplicate files
            name_occurrence = int(db.session.query(db.func.count()).filter(new_item.name == Item.name, new_item.number == Item.number).scalar())
            app.logger.debug("Name_occurence (duplicate detection): {}".format(name_occurrence))

            if name_occurrence:
                version_prefix = uuid4()
                item_name = "{}-{}".format(version_prefix, item.name)
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
            # this branch is typically used for pre-uploading live episodes (no audio)
            else: 
                if not image_file_name:
                    no_error = False

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
        # broadcast episode if asked
        if item.broadcast and no_error:
            if not (play_file and image_file):
                no_error = False
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

        db.session.commit()
        if no_error:
            return make_response(
                jsonify(item_partial_schema.dump(item)), 200, headers
            )
        return "Some error happened, check server logs for details. Note that your media may have been uploaded (to DO and/or Azurcast)."