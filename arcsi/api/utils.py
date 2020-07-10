import os
import unicodedata

from arcsi.model import db
from flask import current_app as app
from werkzeug import secure_filename


def normalise(namestring):
    stripped = unicodedata.normalize("NFD", namestring).encode("ascii", "ignore")
    norms = stripped.decode("utf-8").lower().replace(" ", "_")
    return norms


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
