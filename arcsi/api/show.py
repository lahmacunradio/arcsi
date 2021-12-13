import json
import os
import requests
import io

from datetime import datetime, timedelta
from flask import flash, jsonify, make_response, request, url_for
from flask import current_app as app
from marshmallow import fields, post_load, Schema, ValidationError
from werkzeug import secure_filename

from .utils import archive, process, slug, sort_for
from arcsi.api import arcsi
from arcsi.handler.upload import DoArchive
from arcsi.model import db
from arcsi.model.show import Show
from arcsi.model.user import User
from arcsi.api.item import items_schema, item_archive_schema, Item


class ShowDetailsSchema(Schema):
    id = fields.Int()
    name = fields.Str(required=True)
    active = fields.Boolean(required=True)
    name = fields.Str(required=True)
    description = fields.Str(required=True)
    cover_image_url = fields.Str(dump_only=True)
    language = fields.Str(max=5)
    playlist_name = fields.Str()
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
            only=(
                "description",
                "name",
                "play_file_name",
                "play_date",
                "image_url",
                "download_count"
            ),
        ),
        dump_only=True,
    )
    users = fields.List(
        fields.Nested(
            "UserDetailsSchema",
            only=("id", "name", "email"),
        ),
        required=True,
    )

    @post_load
    def make_show(self, data, **kwargs):
        return Show(**data)


show_schema = ShowDetailsSchema(only=("id", "name", "active", "description",
                                    "cover_image_url", "playlist_name", "items",
                                    "language", "frequency", "day", "start",
                                    "end", "archive_lahmastore_base_url", "users"))
show_archive_schema = ShowDetailsSchema(only=("name", "cover_image_url", 
                                                    "day", "start", "end",
                                                    "frequency", "language",
                                                    "active", "description",
                                                    "items"))
show_partial_schema = ShowDetailsSchema(partial=True)
shows_schema = ShowDetailsSchema(many=True)
shows_schedule_schema = ShowDetailsSchema(many=True, 
                                                   only=("active", "name", "cover_image_url",
                                                         "day", "start", "end",
                                                         "description", "archive_lahmastore_base_url"))
shows_archive_schema = ShowDetailsSchema(many=True, 
                                                   only=("active", "name", "cover_image_url",
                                                   "description", "archive_lahmastore_base_url"))

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
    return shows_schema.dumps(shows)

@arcsi.route("/show/all_schedule", methods=["GET"])
def list_shows_for_schedule():
    do = DoArchive()
    shows = Show.query.all()
    for show in shows:
        if show.cover_image_url:
            show.cover_image_url = do.download(
                show.archive_lahmastore_base_url, show.cover_image_url
            )
    return shows_schedule_schema.dumps(shows)


@arcsi.route("/show/all_page", methods=["GET"])
def list_shows_page():
    do = DoArchive()
    shows = Show.query.all()
    for show in shows:
        if show.cover_image_url:
            show.cover_image_url = do.download(
                show.archive_lahmastore_base_url, show.cover_image_url
            )
    return shows_archive_schema.dumps(shows)

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
    err = show_schema.validate(show_metadata)
    if err:
        return make_response(
            jsonify("Invalid data sent to add show, see: {}".format(err)), 500, headers
        )
    else:
        # host = User.query.filter_by(id=show_metadata["users"]).first()
        show_metadata = show_schema.load(show_metadata)
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
                cover_image_name = process(
                    archive_base=new_show.archive_lahmastore_base_url,
                    archive_idx=0,
                    archive_file=request.files["image_file"],
                    archive_name=(new_show.name, "cover"),
                )
                if cover_image_name:
                    new_show.cover_image_url = archive(
                        archive_base=new_show.archive_lahmastore_base_url,
                        archive_idx=0,
                        archive_file_name=cover_image_name,
                    )

        db.session.commit()

        return make_response(
            jsonify(show_schema.dump(new_show)),
            200,
            headers,
        )


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
    err = show_partial_schema.validate(show_metadata)
    if err:
        return make_response(
            jsonify("Invalid data sent to edit show, see: {}".format(err)),
            500,
            headers,
        )
    else:
        # TODO edit uploaded media
        show_metadata = show_schema.load(show_metadata)
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
                cover_image_name = process(
                    archive_base=show.archive_lahmastore_base_url,
                    archive_idx=0,
                    archive_file=request.files["image_file"],
                    archive_name=(show.name, "cover"),
                )
                if cover_image_name:
                    show.cover_image_url = archive(
                        archive_base=show.archive_lahmastore_base_url,
                        archive_idx=0,
                        archive_file_name=cover_image_name,
                    )

        db.session.commit()
        return make_response(
            jsonify(show_partial_schema.dump(show)), 200, headers
        )

@arcsi.route("show/<id>", methods=["GET"])
def view_show(id):
    do = DoArchive()
    show_query = Show.query.filter_by(id=id)
    show = show_query.first()
    if show:
        if show.cover_image_url:
            show.cover_image_url = do.download(
                show.archive_lahmastore_base_url, show.cover_image_url
            )
        # Display episodes by date in descending order
        # We need to sort nested: episode list of the full object then re-apply that part
        serial_show = show_schema.dump(show)
        date_desc_episodes = sort_for(serial_show["items"], "play_date", "desc")
        serial_show["items"] = date_desc_episodes

        return serial_show
    else:
        return make_response("Show not found", 404, headers)

# We use this route on the legacy front-end show page
@arcsi.route("show/<string:show_slug>/archive", methods=["GET"])
def view_show_archive(show_slug):
    do = DoArchive()
    show_query = Show.query.filter_by(archive_lahmastore_base_url=show_slug)
    show = show_query.first_or_404()
    if show:
        show_json = show_schema.dump(show)
        show_items = [
            show_item
            for show_item in show_json["items"]
            if datetime.strptime(show_item.get("play_date"), "%Y-%m-%d")
            + timedelta(days=1)
            < datetime.today()
        ]
        for show_item in show_items:
            show_item["image_url"] = do.download(
                show.archive_lahmastore_base_url, show_item["image_url"]
            )
        return json.dumps(show_items)
    else:
        return make_response("Show not found", 404, headers)
    #show = show_query.first()
    #if show:
    #    show_items = show.items.filter(Item.play_date < datetime.today() - timedelta(days=1)).all()
    #    return items_schema.dump(show_items)
    #else:
    #    return make_response("Show episodes not found", 404, headers)

# This will be the one that we are gonna use at the new page 
@arcsi.route("show/<string:show_slug>/page", methods=["GET"])
def view_show_page(show_slug):
    show_query = Show.query.filter_by(archive_lahmastore_base_url=show_slug)
    show = show_query.first()
    if show:
        # subquery = session.query(Item.id).filter(blabla -timedelta(day=1)).all().subquery()
        # query = session.query(Show).filter_by(blabla).(Item.id.in_(subquery))
        show.items.filter(Item.play_date < datetime.today() - timedelta(days=1)).all()
        return show_archive_schema.dump(show)
    else:
        return make_response("Show not found", 404, headers)


@arcsi.route("show/<string:show_slug>/episode/<string:episode_slug>", methods=["GET"])
def view_episode_archive(show_slug, episode_slug):
    episode_slug = episode_slug + ".mp3"
    show_query = Show.query.filter_by(archive_lahmastore_base_url=show_slug)
    show = show_query.first_or_404()
    for i in show.items:
        if i.play_file_name == episode_slug:
            return item_archive_schema.dump(i)
    return make_response("Episode not found", 404, headers)