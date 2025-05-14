import os
from datetime import datetime, timedelta
from uuid import uuid4

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


def broadcast_episode(
    item, play_file, image_file, image_file_name, error, error_message
):
    if not (play_file and image_file):
        error = True
        error_message = "ERROR: Both image and audio input are required if broadcast (Azuracast) is set"
        app.logger.debug(error_message)
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
            error = True
            error_message = "ERROR: Item could not be uploaded to Azuracast"
            app.logger.debug(error_message)

            # TODO some mp3 error
            # TODO Maybe I used vanilla mp3 not from azuracast
            # item_audio_obj = MP3(item_path)
            # return item_audio_obj.filename
            # item_length = item_audio_obj.info.length
    return item, error, error_message


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


def process_files(
    request,
    item,
    name_occurrence,
    play_file,
    image_file,
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
                archive_base=item.shows[0].archive_lahmastore_base_url,
                archive_idx=item.number,
                archive_file=play_file,
                archive_file_name=(item.shows[0].name, item_name),
            )

    if request.files["image_file"]:
        if request.files["image_file"] != "":
            image_file = request.files["image_file"]

            image_file_name = save_file(
                archive_base=item.shows[0].archive_lahmastore_base_url,
                archive_idx=item.number,
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
    return item, play_file, image_file, image_file_name, error, error_message


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
            app.logger.debug(
                "STATUS/SAVE FILE: archive_file_path: {}".format(archive_file_path)
            )
            archive_file.save(archive_file_path)
            app.logger.debug("STATUS/SAVE FILE: archive_file: {}".format(archive_file))
            return formed_file_name


def archive_files(item, play_file, image_file, image_file_name, error, error_message):
    # archive files if asked
    if (error == False) and (play_file or image_file):
        if image_file_name:
            item.image_url = archive(
                archive_base=item.shows[0].archive_lahmastore_base_url,
                archive_file_name=image_file_name,
                archive_idx=item.number,
            )
            if not item.image_url:
                error = True
                error_message = "ERROR: Image could not be uploaded to storage"
                app.logger.debug(error_message)

        if item.play_file_name:
            item.archive_lahmastore_canonical_url = archive(
                archive_base=item.shows[0].archive_lahmastore_base_url,
                archive_file_name=item.play_file_name,
                archive_idx=item.number,
            )
            if item.archive_lahmastore_canonical_url:
                # Only set archived if there is audio data otherwise it's live episode
                item.archived = True
            else:  # Upload didn't succeed
                error = True
                error_message = "ERROR: Audio could not be uploaded to storage"
                app.logger.debug(error_message)
    return item, error, error_message


def archive(archive_base, archive_file_name, archive_idx):
    do = DoArchive()

    archive_file_path = media_path(archive_base, str(archive_idx), archive_file_name)
    archive_url = do.upload(archive_file_path, archive_base, archive_idx)

    return archive_url


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


def get_managed_show(user, id):
    managed_show = (
        Show.query.filter(Show.users.contains(user)).filter(Show.id == id).all()
    )
    return managed_show


def get_items():
    items = Item.query.all()
    return items


def get_managed_items(user):
    managed_shows = get_managed_shows(user)
    managed_items = []
    for managed_show in managed_shows:
        managed_items_for_current_show = Item.query.filter(
            Item.shows.contains(managed_show)
        ).all()
        managed_items.extend(managed_items_for_current_show)
    return managed_items


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
        return get_show_items(show, already_aired_items, latest)
    else:
        return get_show_items(show, items, latest)


def get_show_items(show, items, latest):
    do = DoArchive()
    if latest:
        items = items[0]
        items["image_url"] = do.download(
            show.archive_lahmastore_base_url, items["image_url"]
        )
        items["name_slug"] = normalise(items["name"])
        return items
    else:
        for item in items:
            item["image_url"] = do.download(
                show.archive_lahmastore_base_url, item["image_url"]
            )
            item["name_slug"] = normalise(item["name"])
        return items
