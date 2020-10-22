import json
import os
import requests
import io

from flask import flash, jsonify, make_response, request, url_for
from flask import current_app as app
from marshmallow import fields, post_load, Schema, ValidationError
from werkzeug import secure_filename

from .utils import media_path, slug, process_image
from arcsi.api import arcsi
from arcsi.handler.upload import DoArchive
from arcsi.model import db
from arcsi.model.item import Item
from arcsi.model.show import Show
from arcsi.model.user import User

class ShowDetailsSchema(Schema):
    id = fields.Int()
    active = fields.Boolean(required=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    language = fields.Str(max=5)
    playlist_name = fields.Str()
    cover_image_url = fields.Str(dump_only=True)
    frequency = fields.Int(min=1, max=1)
    week = fields.Int()
    day = fields.Int()
    start = fields.Time()
    end = fields.Time()
    archive_lahmastore = fields.Boolean(required=True)
    archive_lahmastore_base_url = fields.Str(dump_only=True)
    archive_mixcloud = fields.Boolean(required=True)
    archive_mixcloud_base_url = fields.Str(dump_only=True)
    items = fields.List(
        fields.Nested(
            "ItemDetailsSchema",
            only=("id", "archived", "description", "name", "number", "play_date", "image_url"),
        ),
        dump_only=True,
    )
    users = fields.List(
        fields.Nested("UserDetailsSchema", only=("id", "name", "email"),), required=True
    )

    @post_load
    def make_show(self, data, **kwargs):
        return Show(**data)


show_details_schema = ShowDetailsSchema()
show_details_partial_schema = ShowDetailsSchema(partial=True)
many_show_details_schema = ShowDetailsSchema(many=True)

headers = {"Content-Type": "application/json"}

@arcsi.route("/show", methods=["GET"])
@arcsi.route("/show/all", methods=["GET"])
def list_shows():
    do = DoArchive()
    shows = Show.query.all()
    for show in shows:
        if show.cover_image_url:
            show.cover_image_url = do.download(
                show.archive_lahmastore_base_url, show.cover_image_url
            )
    return many_show_details_schema.dumps(shows)


@arcsi.route("/show/<id>", methods=["GET"])
def view_show(id):
    do = DoArchive()
    show_query = Show.query.filter_by(id=id)
    show = show_query.first_or_404()
    if show:
        if show.cover_image_url:
            show.cover_image_url = do.download(
                show.archive_lahmastore_base_url, show.cover_image_url
            )
        return show_details_schema.dump(show)
    else:
        return make_response("Show not found", 404, headers)


@arcsi.route("/show/<string:slug>/archive", methods=["GET"])
def view_archive(slug):
    do = DoArchive()
    # TODO instead of json filtering,
    # write actual query
    # joining shows and items
    # so we can limit date etc.
    show_query = Show.query.filter_by(archive_lahmastore_base_url=slug)
    # item_query = Item.query.filter_by(parent_show=)
    show = show_query.first_or_404()
    if show:
        show_json = show_details_schema.dump(show)
        show_items = show_json["items"]
        for show_item in show_items:
            show_item["image_url"] = do.download(show.archive_lahmastore_base_url, show_item["image_url"])
        return json.dumps(show_items)
    else:
        return make_response("Show not found", 404, headers)


# TODO /item/<uuid>/add route so that each upload has unique id to begin with
# no need for different methods for `POST` & `PUT`
@arcsi.route("/show/add", methods=["POST"])
def add_show():
    if request.is_json:
        return make_response(
            jsonify("Only accepts multipart/form-data for now, sorry"), 503, headers
        )
    # work around ImmutableDict type
    show_metadata = request.form.to_dict()
    # TODO see item.py same line
    show_metadata["users"] = [
        {
            "id": show_metadata["users"],
            "name": show_metadata["user_name"],
            "email": show_metadata["user_email"],
        }
    ]
    show_metadata.pop("user_name", None)
    show_metadata.pop("user_email", None)

    # validate payload
    err = show_details_schema.validate(show_metadata)
    if err:
        return make_response(
            jsonify("Invalid data sent to add show, see: {}".format(err)), 500, headers
        )
    else:
        # host = User.query.filter_by(id=show_metadata["users"]).first()
        show_metadata = show_details_schema.load(show_metadata)
        new_show = Show(
            active=show_metadata.active,
            name=show_metadata.name,
            description=show_metadata.description,
            language=show_metadata.language,
            playlist_name=show_metadata.playlist_name,
            frequency=show_metadata.frequency,
            week=show_metadata.week,
            day=show_metadata.day,
            start=show_metadata.start,
            end=show_metadata.end,
            archive_lahmastore=show_metadata.archive_lahmastore,
            archive_lahmastore_base_url=slug(show_metadata.name),
            archive_mixcloud=show_metadata.archive_mixcloud,
            # archive_mixcloud_base_url=archive_mixcloud_base_url,
            users=db.session.query(User)
            .filter(User.id.in_((user.id for user in show_metadata.users)))
            .all(),
        )

        db.session.add(new_show)
        db.session.flush()

        if request.files:
            if request.files["image_file"]:
                process_image(request.files["image_file"], new_show)

        db.session.commit()

        return make_response(jsonify(show_details_schema.dump(new_show)), 200, headers,)


@arcsi.route("/show/<id>", methods=["DELETE"])
def delete_show(id):
    show_query = Show.query.filter_by(id=id)
    show_query.delete()
    db.session.commit()
    return make_response("Deleted show successfully", 200, headers)


@arcsi.route("/show/<id>", methods=["POST"])
def edit_show(id):
    show_query = Show.query.filter_by(id=id)
    show = show_query.first_or_404()

    # work around ImmutableDict type
    show_metadata = request.form.to_dict()

    # TODO see item.py same line
    show_metadata["users"] = [
        {
            "id": show_metadata["users"],
            "name": show_metadata["user_name"],
            "email": show_metadata["user_email"],
        }
    ]
    show_metadata.pop("user_name", None)
    show_metadata.pop("user_email", None)

    # validate payload
    err = show_details_partial_schema.validate(show_metadata)
    if err:
        return make_response(
            jsonify("Invalid data sent to edit show, see: {}".format(err)),
            500,
            headers,
        )
    else:
        # TODO edit uploaded media
        show_metadata = show_details_schema.load(show_metadata)
        show.active = show_metadata.active
        show.name = show_metadata.name
        show.description = show_metadata.description
        show.language = show_metadata.language
        show.playlist_name = show_metadata.playlist_name
        show.frequency = show_metadata.frequency
        show.week = show_metadata.week
        show.day = show_metadata.day
        show.start = show_metadata.start
        show.end = show_metadata.end
        show.archive_lahmastore = show_metadata.archive_lahmastore
        show.archive_lahmastore_base_url = slug(show_metadata.name)
        show.archive_mixcloud = show_metadata.archive_mixcloud
        show.users = (
            db.session.query(User)
            .filter(User.id.in_((user.id for user in show_metadata.users)))
            .all()
        )

        db.session.add(show)
        db.session.flush()

        if request.files:
            if request.files["image_file"]:
                process_image(request.files["image_file"], show)

        db.session.commit()
        return make_response(
            jsonify(show_details_partial_schema.dump(show)), 200, headers
        )

