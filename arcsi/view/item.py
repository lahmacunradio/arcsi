import requests

from flask import current_app as app
from flask import render_template, url_for
from flask_login import current_user
from flask_security import roles_accepted

from arcsi.view import router


@router.route("/item/all")
def list_items():
    if (current_user.has_role("admin")):
        result = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_items"), headers = {"Authentication-Token": current_user.get_auth_token()})
        items = result.json()
    else:
        items = []
    return render_template("item/list.html", items=items)


@router.route("/item/add", methods=["GET"])
@roles_accepted("admin", "host")
def add_item():
    shows = {}

    if not current_user.has_role("admin") and not current_user.shows.all():
        # TODO error handling
        return "add new show first"

    if current_user.has_role("admin"):
        result = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_shows"), headers = {"Authentication-Token": current_user.get_auth_token()})
        shows = result.json()

    shows_sorted = sorted(shows, key=lambda k: k['name'])
    return render_template("item/add.html", shows=shows_sorted)


@router.route("/item/<id>", methods=["GET"])
def view_item(id):
    if (current_user.has_role("admin")):
        relpath = url_for("arcsi.view_item", id=id)
        item = requests.get(app.config["APP_BASE_URL"] + relpath, headers = {"Authentication-Token": current_user.get_auth_token()})
        item_json = item.json()
        #Check legacy None values if no image has been uploaded and change it to empty string so that the renderer doesn't throw error
        if item_json["image_url"] == None:
            item_json["image_url"] = ""
        # use listen API to get the audio URL (HTTP response)
        audiofile_URL_response = requests.get(app.config["APP_BASE_URL"] + relpath + "/listen", headers = {"Authentication-Token": current_user.get_auth_token()})
        audiofile_URL = audiofile_URL_response.text
        # pass the audio URL to the template (text part of HTTP response)
    else:
        item_json = []
        audiofile_URL = ""
    return render_template("item/view.html", item=item_json, audiofile_URL=audiofile_URL)


@router.route("/item/<id>/edit", methods=["GET"])
@roles_accepted("admin", "host", "guest")
def edit_item(id):
    relpath = url_for("arcsi.view_item", id=id)
    item = requests.get(app.config["APP_BASE_URL"] + relpath, headers = {"Authentication-Token": current_user.get_auth_token()})
    item_json = item.json()
    shows = {}
    if current_user.has_role("admin"):
        result = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_shows"), headers = {"Authentication-Token": current_user.get_auth_token()})
        shows = result.json()
    shows_sorted = sorted(shows, key=lambda k: k['name'])
    return render_template("item/edit.html", item=item_json, shows=shows_sorted)
