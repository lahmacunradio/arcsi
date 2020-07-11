import json
import os
import requests
import io

from mutagen.id3 import APIC, ID3
from mutagen.mp3 import MP3

from flask import flash, jsonify, make_response, redirect, request, send_file, url_for
from marshmallow import fields, post_load, Schema, ValidationError


from .utils import dict_to_obj, media_path, normalise
from arcsi.api import arcsi
from arcsi.handler.upload import AzuraArchive, DoArchive
from arcsi.model import db
from arcsi.model.item import Item
from arcsi.model.show import Show


class ItemDetailsSchema(Schema):
    id = fields.Int()
    number = fields.Int(required=True)
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
        fields.Nested("ShowDetailsSchema", only=("id", "name"),), required=True,
    )

    @post_load
    def make_item(self, data, **kwargs):
        return Item(**data)


item_details_schema = ItemDetailsSchema()
item_details_partial_schema = ItemDetailsSchema(partial=True,)
many_item_details_schema = ItemDetailsSchema(many=True)

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
    return many_item_details_schema.dumps(items)


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
        return item_details_schema.dump(item)
    else:
        return make_response("Item not found", 404, headers)


@arcsi.route("/item", methods=["POST"])
def add_item():
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
    err = item_details_schema.validate(item_metadata)
    if err:
        return make_response(
            jsonify("Invalid data sent to add item, see: {}".format(err)), 500, headers
        )
    else:
        item_metadata = item_details_schema.load(item_metadata)
        download_count = 0
        length = 0
        archived = False
        image_url = None
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

        db.session.add(new_item)
        db.session.flush()

        if request.files:
            if request.files["image_file"]:
                image_file = request.files["image_file"]
                image_file_name = normalise(image_file.filename)
                if image_file_name != "":
                    image_file_path = media_path(
                        shows[0].archive_lahmastore_base_url,
                        str(new_item.number),
                        image_file_name,
                    )
                    image_file.save(image_file_path)
                    do = DoArchive()
                    # TODO try / except
                    new_item.image_url = do.upload(
                        image_file_path,
                        shows[0].archive_lahmastore_base_url,
                        new_item.number,
                    )
            if request.files["play_file"]:
                play_file = request.files["play_file"]
                play_file_name = normalise(play_file.filename)
                if play_file_name != "":
                    play_file_path = media_path(
                        shows[0].archive_lahmastore_base_url,
                        str(new_item.number),
                        play_file_name,
                    )
                    play_file.save(play_file_path)
                    new_item.play_file_name = play_file_name

                    # TODO error handling if broadcast || archive_lahmastore but no play_file
                    if new_item.broadcast:
                        az = AzuraArchive(
                            play_file_path,
                            new_item.play_file_name,
                            image_file_path,
                            shows[0].name,
                            new_item.name,
                            shows[0].playlist_name,
                        )

                        # TODO find image -- fallback to show cover; handle this if-tree better
                        # TODO embed metadata regardless of there's image or not f.e. title && artist
                        if new_item.image_url:
                            episode_update = az.embedded_metadata()
                        station_upload = az.upload()
                        if station_upload:
                            episode_playlist = az.assign_playlist()
                            if episode_playlist:
                                # TODO change all other episode airing to false
                                new_item.airing = True

                    if new_item.archive_lahmastore:
                        do = DoArchive()
                        new_item.archive_lahmastore_canonical_url = do.upload(
                            play_file_path,
                            shows[0].archive_lahmastore_base_url,
                            new_item.number,
                        )
                        new_item.archived = True

            # TODO some mp3 error
            # TODO Maybe I used vanilla mp3 not from azuracast
            # item_audio_obj = MP3(item_path)
            # return item_audio_obj.filename
            # item_length = item_audio_obj.info.length

        db.session.commit()

        return make_response(jsonify(item_details_schema.dump(new_item)), 200, headers,)


@arcsi.route("/item/<id>/download", methods=["GET"])
def download_play_file(id):
    do = DoArchive()
    item_query = Item.query.filter_by(id=id)
    item = item_query.first_or_404()
    presigned = do.download(
        item.shows[0].archive_lahmastore_base_url, item.archive_lahmastore_canonical_url
    )
    req = requests.get(presigned)
    media_item = io.BytesIO(req.content)
    return send_file(
        media_item, as_attachment=True, attachment_filename=item.play_file_name
    )


@arcsi.route("/item/<id>", methods=["DELETE"])
def delete_item(id):
    item_query = Item.query.filter_by(id=id)
    item = item_query.first_or_404()
    item_query.delete()
    db.session.commit()
    return make_response("Deleted item successfully", 200, headers)


@arcsi.route("/item/<id>", methods=["POST"])
def edit_item(id):
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
    err = item_details_schema.validate(item_metadata)
    if err:
        return make_response(
            jsonify("Invalid data sent to edit item, see: {}".format(err)),
            500,
            headers,
        )
    else:
        # TODO edit uploaded media -- remove re-up etc.
        # TODO broadcast / airing
        item_metadata = item_details_schema.load(item_metadata)
        item.number = item_metadata.number
        item.name = item_metadata.name
        item.description = item_metadata.description
        item.language = item_metadata.language
        item.play_date = item_metadata.play_date
        item.live = item_metadata.live
        # item.broadcast = item_metadata.broadcast
        # item.airing = item_metadata.airing
        item.uploader = item_metadata.uploader
        item.archive_lahmastore = item_metadata.archive_lahmastore
        item.archive_mixcloud = item_metadata.archive_mixcloud
        if item.archive_lahmastore or item.archive_mixcloud:
            item.archived = True
        else:
            item.archived = False
        # conflict between shows from detached object load(item_metadata) added to session vs original persistent object item from query
        item.shows = (
            db.session.query(Show)
            .filter(Show.id.in_((show.id for show in item_metadata.shows)))
            .all()
        )
        db.session.commit()
        return make_response(
            jsonify(item_details_partial_schema.dump(item)), 200, headers
        )
