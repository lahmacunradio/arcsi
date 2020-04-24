import json
import os

from mutagen.mp3 import MP3

from flask import flash, jsonify, make_response, redirect, request, url_for
from flask import current_app as app
from werkzeug import secure_filename

from arcsi.api import arcsi
from arcsi.model.item import db, Item

# TODO /item/<uuid>/add route so that each upload has unique id to begin with
# no need for different methods for `POST` & `PUT`
@arcsi.route("/item/add", methods=["POST"])
def add_item():

    headers = {"Content-Type": "application/json"}
    if request.is_json:
        return make_response(
            jsonify("Only accepts multipart/form-data for now, sorry"), 503, headers
        )
    # We should let uploads with empty data right? Maybe flag it
    # if "item" not in request.files:
    #     return make_response(jsonify("No item selected"), 503, headers)
    item = request.files["item"]
    item_name = item.filename
    item_length = 0
    if item_name != "":
        item_path = os.path.join(
            app.config["UPLOAD_FOLDER"], secure_filename(item_name)
        )
        item.save(item_path)
        # TODO some mp3 error
        # item_audio_obj = MP3(item_path)
        # return item_audio_obj.filename
        # item_length = item_audio_obj.info.length
        item_length = 0
    # work around ImmutableDict type
    item_metadata = request.form.to_dict()
    archive_url = None

    new_item = Item(
        item_metadata["showname"],
        item_metadata["showcover"],
        item_metadata["epnumber"],
        item_metadata["eptitle"],
        item_length,
        item_metadata["epcover"],
        item_metadata["epdate"],
        item_name,
        archive_url,
    )

    db.session.add(new_item)
    db.session.commit()

    return make_response(
        jsonify(
            {
                "return_item_id": new_item.id,
                "return_show_name": new_item.show_name,
                "return_show_cover": new_item.show_cover_url,
                "return_episode_number": new_item.episode_number,
                "return_episode_title": new_item.episode_title,
                "return_episode_length": new_item.episode_length,
                "return_episode_cover": new_item.episode_cover_url,
                "return_episode_date": new_item.episode_date,
                "return_episode_file": new_item.source_url,
                "return_episode_archive": new_item.archive_url,
            }
        ),
        200,
        headers,
    )
