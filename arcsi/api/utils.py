import os

from arcsi.handler.upload import AzuraArchive, DoArchive
from arcsi.model import db
from arcsi.model.show import Show
from flask import current_app as app
from slugify import slugify
from werkzeug import secure_filename

CONNECTER = "_"
DELIMITER = "-"
DOT = "."


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


def show_or_not(item_obj):
    return True if isinstance(item_obj, Show) else False


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


def broadcast_audio(archive_base, archive_idx, broadcast_file_name, broadcast_playlist, broadcast_show, broadcast_title, image_file_name):
    broadcast_file_path = media_path(
        archive_base,
        str(archive_idx),
        broadcast_file_name
    )
    image_file_path = media_path(
        archive_base,
        str(archive_idx),
        image_file_name
    )
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


def process(archive_base, archive_idx, archive_file, archive_name):
    archive_file_name = form_filename(archive_file, archive_name)
    if archive_file_name != "":
        archive_file_path = media_path(
            archive_base, str(archive_idx), archive_file_name
        )
        archive_file.save(archive_file_path)
        return archive_file_name
    else:
        return None
    

def archive(archive_base, archive_file_name, archive_idx):
    do = DoArchive()

    archive_file_path = media_path(
        archive_base, str(archive_idx), archive_file_name
    )
    archive_url = do.upload(archive_file_path, archive_base, archive_idx)
    
    return archive_url
