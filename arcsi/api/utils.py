import os
from uuid import uuid4

from flask import request
from flask import current_app as app
from slugify import slugify
from werkzeug.utils import safe_join, secure_filename

from arcsi.model import db

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


def comma_separated_params_to_list(param):
    result = []
    for val in param.split(","):
        if val:
            result.append(val)
    return result
