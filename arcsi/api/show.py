import json

from datetime import datetime, timedelta
from flask import jsonify, make_response, request
from flask import current_app as app
from flask_security import auth_token_required, roles_required
from marshmallow import fields, post_load, Schema
from sqlalchemy import func

from .utils import archive, get_shows, save_file, slug, sort_for, normalise
from . import arcsi
from arcsi.handler.upload import DoArchive
from arcsi.model import db
from arcsi.model.show import Show
from arcsi.model.user import User
from arcsi.api.item import item_archive_schema


class ShowDetailsSchema(Schema):
    id = fields.Int()
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
                "id",
                "description",
                "number",
                "name",
                "name_slug",
                "play_file_name",
                "play_date",
                "image_url",
                "archived",
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


show_schema = ShowDetailsSchema()
show_archive_schema = ShowDetailsSchema(only=("id", "active", "name", "description", "cover_image_url", 
                                                    "day", "start", "end", "frequency", "language",
                                                    "playlist_name", "archive_lahmastore_base_url", "archive_mixcloud_base_url", "items"))
show_partial_schema = ShowDetailsSchema(partial=True)
shows_schema = ShowDetailsSchema(many=True)
shows_schedule_schema = ShowDetailsSchema(many=True, exclude=("items",))
shows_schedule_by_schema = ShowDetailsSchema(many=True, 
                                                    only=("id", "active", "name", "description", "cover_image_url", 
                                                    "day", "start", "end", "frequency", "language",
                                                    "playlist_name", "archive_lahmastore_base_url", "items"))
shows_archive_schema = ShowDetailsSchema(many=True, 
                                                    only=("id", "active", "name", "description", "cover_image_url",
                                                    "playlist_name", "archive_lahmastore_base_url"))

headers = {"Content-Type": "application/json"}


@arcsi.route("/show", methods=["GET"])
# We use this route on the legacy for a massive shows query
@arcsi.route("/show/all", methods=["GET"])
@auth_token_required
def list_shows():
    return shows_schema.dumps(get_shows())


@arcsi.route("/show/all_without_items", methods=["GET"])
@auth_token_required
def list_shows_without_items():
    return shows_schedule_schema.dumps(get_shows())   


@arcsi.route("/show/schedule", methods=["GET"])
@auth_token_required
def list_shows_for_schedule():
    do = DoArchive()
    shows = Show.query.filter(Show.active == True).all()
    for show in shows:
        if show.cover_image_url:
            show.cover_image_url = do.download(
                show.archive_lahmastore_base_url, show.cover_image_url
            )
    return shows_schedule_schema.dumps(shows)    


@arcsi.route("/show/schedule_by", methods=["GET"])
@auth_token_required
def list_shows_for_schedule_by():
    do = DoArchive()
    day = request.args.get('day', 1, type=int)
    shows = Show.query.filter(Show.day == day and Show.active == True).all()
    shows_json = shows_schedule_by_schema.dump(shows)
    # iterate through shows
    for show_json in shows_json:
        if show_json["cover_image_url"]:
            show_json["cover_image_url"] = do.download(
                show_json["archive_lahmastore_base_url"], show_json["cover_image_url"]
            )
        if show_json["items"]:
            latest_item_found = False
            # iterate through show's items
            for item in show_json["items"]:
                # search for the first one which is archived & already aired
                if (latest_item_found == False and
                item["archived"] == True and
                ((datetime.strptime(item["play_date"], "%Y-%m-%d") + timedelta(days=1)) < datetime.today())):
                    latest_item_found = True
                    item["image_url"] = do.download(
                            show_json["archive_lahmastore_base_url"], item["image_url"]
                    )
                    item["name_slug"] = normalise(item["name"])
                    show_json["items"] = item
            # if there is no archived show return empty array
            if (latest_item_found == False):
                show_json["items"] = []
    return json.dumps(shows_json)


# We are gonna use this on the new page as the show/all
@arcsi.route("/show/list", methods=["GET"])
@auth_token_required
def list_shows_page():
    return shows_archive_schema.dumps(get_shows())


# TODO /item/<uuid>/add route so that each upload has unique id to begin with
# no need for different methods for `POST` & `PUT`
@arcsi.route("/show/add", methods=["POST"])
@roles_required("admin")
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
                cover_image_name = save_file(
                    archive_base=new_show.archive_lahmastore_base_url,
                    archive_idx=0,
                    archive_file=request.files["image_file"],
                    archive_file_name=(new_show.name, "cover"),
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
@roles_required("admin")
def delete_show(id):
    show_query = Show.query.filter_by(id=id)
    show_query.delete()
    db.session.commit()
    return make_response("Deleted show successfully", 200, headers)


@arcsi.route("/show/<id>/edit", methods=["POST"])
@roles_required("admin")
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
                cover_image_name = save_file(
                    archive_base=show.archive_lahmastore_base_url,
                    archive_idx=0,
                    archive_file=request.files["image_file"],
                    archive_file_name=(show.name, "cover"),
                )
                if cover_image_name:
                    app.logger.debug("STATUS: Cover image name: {}".format(cover_image_name))
                    show.cover_image_url = archive(
                        archive_base=show.archive_lahmastore_base_url,
                        archive_idx=0,
                        archive_file_name=cover_image_name,
                    )
                    app.logger.debug("STATUS: Cover image url: {}".format(show.cover_image_url))
                else:
                    app.logger.debug("ERROR: Error while uploading cover image.")

        db.session.commit()
        return make_response(
            jsonify(show_partial_schema.dump(show)), 200, headers
        )


@arcsi.route("show/<id>", methods=["GET"])
@auth_token_required
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
        for item in serial_show["items"]:
            item["name_slug"] = normalise(item["name"])

        return serial_show
    else:
        return make_response("Show not found", 404, headers)


# We use this route on the legacy front-end show page
@arcsi.route("show/<string:show_slug>/archive", methods=["GET"])
@auth_token_required
def view_show_archive(show_slug):
    do = DoArchive()
    show_query = Show.query.filter_by(archive_lahmastore_base_url=show_slug)
    show = show_query.first()
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
            show_item["name_slug"]=normalise(show_item["name"])
        return json.dumps(show_items)
    else:
        return make_response("Show not found", 404, headers)


# This will be the one that we are gonna use at the new page 
@arcsi.route("show/<string:show_slug>/page", methods=["GET"])
@auth_token_required
def view_show_page(show_slug):
    do = DoArchive()
    show_query = Show.query.filter_by(archive_lahmastore_base_url=show_slug)
    show = show_query.first()
    if show:
        # subquery = session.query(Item.id).filter(blabla -timedelta(day=1)).all().subquery()
        # query = session.query(Show).filter_by(blabla).(Item.id.in_(subquery))
        if show.cover_image_url:
            show.cover_image_url = do.download(
                show.archive_lahmastore_base_url, show.cover_image_url
            )
        serial_show = show_archive_schema.dump(show)
        show_items = [
            show_item
            for show_item in serial_show["items"]
            if datetime.strptime(show_item.get("play_date"), "%Y-%m-%d")
            + timedelta(days=1)
            < datetime.today()
        ]
        serial_show["items"]=show_items
        for item in serial_show["items"]:
            item["image_url"] = do.download(
                show.archive_lahmastore_base_url, item["image_url"]
            )
            item["name_slug"]=normalise(item["name"])
        return serial_show
    else:
        return make_response("Show not found", 404, headers)


@arcsi.route("show/<string:show_slug>/item/<string:item_slug>", methods=["GET"])
@auth_token_required
def view_episode_archive(show_slug, item_slug):
    do = DoArchive()
    show_query = Show.query.filter_by(archive_lahmastore_base_url=show_slug)
    show = show_query.first_or_404()
    for item in show.items:
        if (normalise(item.name) == item_slug):
            item.image_url = do.download(
                show.archive_lahmastore_base_url, item.image_url
            )
            item.name_slug=item_slug
            return item_archive_schema.dump(item)
    return make_response("Episode not found", 404, headers)


@arcsi.route("/show/search", methods=["GET"])
@auth_token_required
def search_show():
    do = DoArchive()
    page = request.args.get('page', 1, type=int)
    size = request.args.get('size', 12, type=int)
    param = request.args.get('param', "", type=str)
    shows = Show.query.filter(func.lower(Show.name).contains(func.lower(param)) | func.lower(Show.description).contains(func.lower(param))).paginate(page, size, False)
    for show in shows.items:
        if show.cover_image_url:
            show.cover_image_url = do.download(
                show.archive_lahmastore_base_url, show.cover_image_url
            )
    return shows_schedule_schema.dumps(shows.items)
