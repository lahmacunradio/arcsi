import os
from datetime import datetime, timedelta
from flask import request
from flask import current_app as app
from slugify import slugify
from werkzeug.utils import secure_filename

from arcsi.handler.upload import AzuraArchive, DoArchive
from arcsi.model import db
from arcsi.model.show import Show
from arcsi.model.item import Item

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


def media_path(show, number, item_name):
    try:
        os.makedirs("{}/{}/{}".format(app.config["UPLOAD_FOLDER"], show, number))
    except FileExistsError as err:
        pass
    media_file_path = os.path.join(
        app.config["UPLOAD_FOLDER"], show, number, secure_filename(item_name)
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

def broadcast_audio(
    archive_base,
    archive_idx,
    broadcast_file_name,
    broadcast_playlist,
    broadcast_show,
    broadcast_title,
    image_file_name,
):
    broadcast_file_path = media_path(
        archive_base, str(archive_idx), broadcast_file_name
    )
    image_file_path = media_path(archive_base, str(archive_idx), image_file_name)
    az = AzuraArchive(
        broadcast_file_path,
        broadcast_file_name,
        image_file_path,
        broadcast_show,
        broadcast_title,
        broadcast_playlist,
    )

    # TODO find image -- fallback to show cover; handle this if-tree better
    # TODO embed metadata regardless of there's image or not f.e. title && artist
    # file_path but then image_url?? ugly
    if image_file_path:
        episode_update = az.embedded_metadata()
    station_upload = az.upload()
    if station_upload:
        episode_playlist = az.assign_playlist()
        if episode_playlist:
            # TODO change all other episode airing to false
            return True
    return False

def save_file(archive_base, archive_idx, archive_file, archive_file_name):
    formed_file_name = form_filename(archive_file, archive_file_name)
    app.logger.debug("STATUS/SAVE FILE: formed_file_name: {}".format(formed_file_name))
    if not allowed_file(formed_file_name):
        app.logger.debug("STATUS/SAVE FILE: Not allowed file. See ALLOWED_EXTENSIONS")
        return None
    else:
        if formed_file_name == "":
            return None
            app.logger.debug("STATUS/SAVE FILE: File name could not be computed")
        else:
            archive_file_path = media_path(
                archive_base, str(archive_idx), formed_file_name
            )
            app.logger.debug("STATUS/SAVE FILE: archive_file_path: {}".format(archive_file_path))
            archive_file.save(archive_file_path)
            app.logger.debug("STATUS/SAVE FILE: archive_file: {}".format(archive_file))
            return formed_file_name

def archive(archive_base, archive_file_name, archive_idx):
    do = DoArchive()

    archive_file_path = media_path(archive_base, str(archive_idx), archive_file_name)
    archive_url = do.upload(archive_file_path, archive_base, archive_idx)

    return archive_url

def get_items():
    items = Item.query.all()
    return items

def get_managed_items(user):
    managed_shows = Show.query.filter(Show.users.contains(user)).all()
    managed_items = Item.query.filter(Item.shows.contains(managed_shows)).all()
    return managed_items

def get_shows():
    shows = Show.query.all()
    return shows

def get_shows_with_cover():
    do = DoArchive()
    shows = Show.query.all()
    for show in shows:
        if show.cover_image_url:
            show.cover_image_url = do.download(
                show.archive_lahmastore_base_url, show.cover_image_url
            )
    return shows


def get_managed_shows(user):
    managed_shows = Show.query.filter(Show.users.contains(user)).all()
    return managed_shows

def show_item_duplications_number(item):
    existing_items = Show.query.filter(Show.id == item.shows[0].id).first().items
    existing_items_with_same_name = existing_items.filter_by(name=item.name)
    name_occurrence = existing_items_with_same_name.count()
    app.logger.error("Name_occurence (duplicate detection): {}".format(name_occurrence))
    return name_occurrence

def comma_separated_params_to_list(param):
    result = []
    for val in param.split(','):
        if val:
            result.append(val)
    return result

def filter_show_items(show, items, archived, latest):
    items = sorted(items, key=lambda x: x["play_date"], reverse=True)
    if archived:
        already_aired_items = [
            show_item
            for show_item in items
            if (show_item.get("archived") &
                (datetime.strptime(show_item.get("play_date"), "%Y-%m-%d") + timedelta(days=1) < datetime.today()))
        ]
        return get_show_items(show, already_aired_items, latest)
    else:
        return get_show_items(show, items, latest)
        
def get_show_items(show, items, latest):
    do = DoArchive()
    if latest:
        items = items[0]
        items["image_url"] = do.download(show.archive_lahmastore_base_url, items["image_url"])
        items["name_slug"] = normalise(items["name"])
        return items
    else:
        for item in items:
            item["image_url"] = do.download(
                show.archive_lahmastore_base_url, item["image_url"]
            )
            item["name_slug"] = normalise(item["name"])
        return items