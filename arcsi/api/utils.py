import os
from datetime import datetime, timedelta
from uuid import uuid4

from flask import request
from flask import current_app as app
from slugify import slugify
from sqlalchemy import func
from werkzeug.utils import safe_join, secure_filename

from arcsi.handler.archival import (
    get_show_cover_json,
    get_item_fields_json,
    get_show_items,
)

from arcsi.model import db
from arcsi.model.item import Item
from arcsi.model.show import Show
from arcsi.model.tag import Tag

CONNECTER = "_"
DELIMITER = "-"
DOT = "."


def allowed_file(filename):
    return (
        DOT in filename
        and filename.rsplit(DOT, 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )


def sort_for(collection, value, direction="asc"):
    if isinstance(collection, list):
        mod_list = [
            collectible
            for collectible in sorted(collection, key=lambda arg: arg[value])
        ]
        if direction == "desc":
            mod_list.reverse()
        elif direction == "asc":
            pass  # sorted is ascending already
        else:
            raise ValueError("Only accepting `asc` and `desc` as directions")
        return mod_list
    else:
        raise TypeError(
            "Collection should be of type: `List` instead found {}".format(
                type(collection)
            )
        )


def dict_to_obj(dict_name, table):
    show_seq = (k["id"] for k in dict_name)
    obj_list = db.session.query(table).filter(table.id.in_(show_seq)).all()
    return obj_list


def media_path(norms_show_name, episode_number, item_name):
    try:
        os.makedirs(
            "{}/{}/{}".format(
                app.config["UPLOAD_FOLDER"], norms_show_name, episode_number
            )
        )
    except FileExistsError as err:
        pass
    media_file_path = safe_join(
        app.config["UPLOAD_FOLDER"],
        norms_show_name,
        episode_number,
        secure_filename(item_name),
    )
    return media_file_path


def normalise(namestring):
    slugged = slugify(namestring)
    norms = slugged.replace(DELIMITER, CONNECTER)
    return norms


def slug(namestring):
    slugs = slugify(namestring)
    return slugs


def form_filename(file_obj, title_tuple):
    """
    Filename naming schema:
    Use normalised combination of show name and episode name of parent object.
    Join them w/ delimiter.
    Get the extension from file sent to API.
    To get the extension we use rsplit w/ maxsplit=1 to make sure we always get the extension even if there is another dot in the filename.
    """
    ext = file_obj.filename.rsplit(DOT, 1)[1].lower()
    norms_show_name = normalise(title_tuple[0])
    norms_ep_name = normalise(title_tuple[1])
    norms_names = [norms_show_name, norms_ep_name]
    return "{}{}{}".format(DELIMITER.join(norms_names), DOT, ext)


def find_request_params(param, default, type):
    return request.args.get(param, default, type)


def process_files(
    request,
    item,
    name_occurrence,
    image_file_name,
    error,
    error_message,
):
    # Defend against possible duplicate files
    if 0 < name_occurrence:
        version_prefix = uuid4()
        item_name = "{}-{}".format(item.name, version_prefix)
    else:
        item_name = item.name

    # process files first
    if request.files["play_file"]:
        if request.files["play_file"] != "":
            play_file = request.files["play_file"]

            item.play_file_name = save_file(
                norms_show_name=item.shows[0].archive_lahmastore_base_url,
                episode_number=item.number,
                archive_file=play_file,
                archive_file_name=(item.shows[0].name, item_name),
            )

    if request.files["image_file"]:
        if request.files["image_file"] != "":
            image_file = request.files["image_file"]

            image_file_name = save_file(
                norms_show_name=item.shows[0].archive_lahmastore_base_url,
                episode_number=item.number,
                archive_file=image_file,
                archive_file_name=(item.shows[0].name, item_name),
            )

    if item.broadcast:
        # we require both image and audio if broadcast (Azuracast) is set
        if not (image_file_name and item.play_file_name):
            error = True
            error_message = "ERROR: Both image and audio input are required if broadcast (Azuracast) is set"
            app.logger.debug(error_message)
    # this branch is typically used for pre-uploading live episodes (no audio)
    else:
        if not image_file_name:
            error = True
            error_message = "ERROR: You need to add at least an image"
            app.logger.debug(error_message)
    return item, image_file_name, error, error_message


def save_file(norms_show_name, episode_number, archive_file, archive_file_name):
    formed_file_name = form_filename(archive_file, archive_file_name)
    app.logger.debug("STATUS/SAVE FILE: formed_file_name: {}".format(formed_file_name))
    if not allowed_file(formed_file_name):
        app.logger.debug("STATUS/SAVE FILE: Not allowed file. See ALLOWED_EXTENSIONS")
        return None
    else:
        if formed_file_name == "":
            app.logger.debug("STATUS/SAVE FILE: File name could not be computed")
            return None
        else:
            archive_file_path = media_path(
                norms_show_name, str(episode_number), formed_file_name
            )
            app.logger.debug(
                "STATUS/SAVE FILE: archive_file_path: {}".format(archive_file_path)
            )
            archive_file.save(archive_file_path)
            app.logger.debug("STATUS/SAVE FILE: archive_file: {}".format(archive_file))
            return formed_file_name


def cleanup_tmp_files(item):
    if item.play_file_name:
        delete_file(
            norms_show_name=item.shows[0].archive_lahmastore_base_url,
            archive_file_path=item.archive_lahmastore_canonical_url,
        )
    delete_file(
        norms_show_name=item.shows[0].archive_lahmastore_base_url,
        archive_file_path=item.image_url,
    )


def delete_file(norms_show_name, archive_file_path):
    os.remove(
        safe_join(
            app.config["UPLOAD_FOLDER"],
            norms_show_name,
            archive_file_path,
        )
    )
    return True


def get_shows():
    shows = Show.query.all()
    return shows


def get_active_shows_on_given_week(request):
    week = request.args.get("week", 1, type=int)
    abcd_week = week % 4
    return Show.query.filter(Show.active == True).filter(Show.week.any(abcd_week))


def get_shows_with_latest_item(shows, schema):
    shows_json = schema.dump(shows)
    # iterate through shows
    for show_json in shows_json:
        get_show_cover_json(show_json)
        if show_json["items"]:
            latest_item_found = False
            # iterate through show's items
            for item_json in show_json["items"]:
                # search for the first one which is archived & already aired
                if (
                    latest_item_found == False
                    and item_json["archived"] == True
                    and (
                        (
                            datetime.strptime(item_json["play_date"], "%Y-%m-%d")
                            + timedelta(days=1)
                        )
                        < datetime.today()
                    )
                ):
                    latest_item_found = True
                    get_item_fields_json(item_json, show_json)
                    show_json["items"] = item_json
            # if there is no archived show return empty array
            if latest_item_found == False:
                show_json["items"] = []
    return shows_json


def get_managed_show(user, id):
    managed_show = (
        Show.query.filter(Show.users.contains(user)).filter(Show.id == id).all()
    )
    return managed_show


def get_managed_shows(user):
    managed_shows = Show.query.filter(Show.users.contains(user)).all()
    return managed_shows


def get_items():
    items = Item.query.all()
    return items


def search_items(param):
    return (
        Item.query.filter(
            func.lower(Item.name).contains(func.lower(param))
            | func.lower(Item.description).contains(func.lower(param))
        )
        .filter(Item.play_date < datetime.today() - timedelta(days=1))
        .filter(Item.archived == True)
    )


def search_show_items(param):
    return (
        Item.query.join(Item.shows)
        .filter(func.lower(Show.name).contains(func.lower(param)))
        .filter(Item.play_date < datetime.today() - timedelta(days=1))
        .filter(Item.archived == True)
    )


def search_tag_items(param):
    return (
        Item.query.join(Item.tags)
        .filter(func.lower(Tag.clean_name).contains(normalise(param)))
        .filter(Item.play_date < datetime.today() - timedelta(days=1))
        .filter(Item.archived == True)
    )


def search_shows_by_tag(param):
    return Show.query.join(Show.tags).filter(
        func.lower(Tag.clean_name) == (func.lower(param))
    )


def search_items_by_tag(param):
    return (
        Item.query.join(Item.tags)
        .filter(func.lower(Tag.clean_name) == (func.lower(param)))
        .filter(Item.play_date < datetime.today() - timedelta(days=1))
        .filter(Item.archived == True)
    )


def get_managed_items(user):
    managed_shows = get_managed_shows(user)
    managed_items = []
    for managed_show in managed_shows:
        managed_items_for_current_show = Item.query.filter(
            Item.shows.contains(managed_show)
        ).all()
        managed_items.extend(managed_items_for_current_show)
    return managed_items


def read_user_fields(metadata):
    metadata["users"] = [
        {
            "id": metadata["user_id"],
            "name": metadata["user_name"],
            "email": metadata["user_email"],
        }
    ]
    metadata.pop("user_id", None)
    metadata.pop("user_name", None)
    metadata.pop("user_email", None)
    return metadata


def read_week_field(metadata):
    metadata["week"] = [
        week_number.strip() for week_number in metadata["week"].split(",")
    ]
    return metadata


def read_show_field(metadata):
    metadata["shows"] = [{"id": metadata["shows"], "name": metadata["show_name"]}]
    metadata.pop("show_name", None)
    return metadata


def read_tag_field(metadata):
    metadata["tags"] = [
        {"display_name": dis_name.strip()}
        for dis_name in metadata["taglist"].split(",")
    ]
    metadata["tags"] = [dict(t) for t in {tuple(d.items()) for d in metadata["tags"]}]
    metadata.pop("taglist", None)
    return metadata


def show_item_duplications_number(item):
    existing_items = Show.query.filter(Show.id == item.shows[0].id).first().items
    existing_items_with_same_name = existing_items.filter_by(name=item.name)
    name_occurrence = existing_items_with_same_name.count()
    app.logger.error("Name_occurence (duplicate detection): {}".format(name_occurrence))
    return name_occurrence


def comma_separated_params_to_list(param):
    result = []
    for val in param.split(","):
        if val:
            result.append(val)
    return result


def filter_show_items(show, items, archived, latest):
    items = sorted(items, key=lambda x: x["play_date"], reverse=True)
    if archived:
        already_aired_items = [
            show_item
            for show_item in items
            if (
                show_item.get("archived")
                & (
                    datetime.strptime(show_item.get("play_date"), "%Y-%m-%d")
                    + timedelta(days=1)
                    < datetime.today()
                )
            )
        ]
        if 0 < len(already_aired_items):
            return get_show_items(show, already_aired_items, latest)
        else:
            return []
    else:
        return get_show_items(show, items, latest)
