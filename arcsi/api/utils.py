import os
import unicodedata

from arcsi.handler.upload import AzuraArchive, DoArchive
from arcsi.model import db
from arcsi.model.item import Item
from arcsi.model.show import Show
from flask import current_app as app
from slugify import slugify
from werkzeug import secure_filename


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


def slug(namestring):
    slugs = slugify(namestring)
    return slugs


def normalise(namestring):
    stripped = unicodedata.normalize("NFD", namestring).encode("ascii", "ignore")
    norms = stripped.decode("utf-8").lower().replace(" ", "_").replace("#", "_")
    return norms


def archive_audio(play_file_path, item):
    do = DoArchive()
    item.archive_lahmastore_canonical_url = do.upload(
        play_file_path, item.shows[0].archive_lahmastore_base_url, item.number,
    )
    item.archived = True


def broadcast_audio(audio_file_path, item, image_file_path):
    az = AzuraArchive(
        audio_file_path,
        item.play_file_name,
        image_file_path,
        item.shows[0].name,
        item.name,
        item.shows[0].playlist_name,
    )

    # TODO find image -- fallback to show cover; handle this if-tree better
    # TODO embed metadata regardless of there's image or not f.e. title && artist
    # file_path but then image_url?? ugly
    if item.image_url:
        episode_update = az.embedded_metadata()
    station_upload = az.upload()
    if station_upload:
        episode_playlist = az.assign_playlist()
        if episode_playlist:
            # TODO change all other episode airing to false
            item.airing = True


def process_audio(play_file, item, image_file_path):
    play_file_name = normalise(play_file.filename)
    if play_file_name != "":
        play_file_path = media_path(
            item.shows[0].archive_lahmastore_base_url, str(item.number), play_file_name,
        )
        play_file.save(play_file_path)
        item.play_file_name = play_file_name

        # TODO error handling if broadcast || archive_lahmastore but no play_file
        if item.broadcast:
            # if image_file_path:
            # TODO fallback img from show
            # TODO fallback img arcsi default img

            # ughhhh........
            broadcast_audio(play_file_path, item, image_file_path)

        if item.archive_lahmastore:
            # disdain
            archive_audio(play_file_path, item)

        return play_file_path


def process_image(image_file, item):
    image_file_name = normalise(image_file.filename)
    if image_file_name != "":
        if isinstance(item, Show):
            image_file_path = media_path(
                item.archive_lahmastore_base_url, str(0), image_file_name,
            )
        else:
            image_file_path = media_path(
                item.shows[0].archive_lahmastore_base_url,
                str(item.number),
                image_file_name,
            )
        image_file.save(image_file_path)
        do = DoArchive()
        # TODO try / except
        if isinstance(item, Show):
            item.cover_image_url = do.upload(
                image_file_path, item.archive_lahmastore_base_url, 0,
            )
        else:
            item.image_url = do.upload(
                image_file_path, item.shows[0].archive_lahmastore_base_url, item.number,
            )
        return image_file_path


def process_media(request_files, item):
    if request_files["image_file"]:
        image_file_path = process_image(request_files["image_file"], item)
    if request_files["play_file"]:
        if image_file_path:
            audio_file_path = process_audio(
                request_files["play_file"], item, image_file_path
            )

