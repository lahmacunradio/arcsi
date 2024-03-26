import requests

from flask import current_app as app
from flask import render_template, url_for
from flask_login import current_user
from flask_security import login_required, roles_accepted


from arcsi.api import archon_view_item, listen_play_file, archon_list_items, frontend_list_shows_without_items
from arcsi.view import router


@router.route("/item/all")
@login_required
def list_items():
    items = archon_list_items()
    return render_template("item/list.html", items=items)


@router.route("/item/add", methods=["GET"])
@roles_accepted("admin", "host")
def add_item():
    shows = {}

    if not current_user.has_role("admin") and not current_user.shows.all():
        # TODO error handling
        return "add new show first"

    if current_user.has_role("admin"):
        shows = frontend_list_shows_without_items()

    shows_sorted = sorted(shows, key=lambda k: k['name'])
    return render_template("item/add.html", shows=shows_sorted)


@router.route("/item/<id>", methods=["GET"])
@login_required
def view_item(id):
    item = archon_view_item(id)
    if (hasattr(item, 'status_code') and item.status_code == 404):
        return "Episode not found"
    #Check legacy None values if no image has been uploaded and change it to empty string so that the renderer doesn't throw error
    if item["image_url"] == None:
        item["image_url"] = ""
    # use listen API to get the audio URL (HTTP response)
    audiofile_URL = listen_play_file(id)
    
    # pass the audio URL to the template (text part of HTTP response)
    return render_template("item/view.html", item=item, audiofile_URL=audiofile_URL)


@router.route("/item/<id>/edit", methods=["GET"])
@roles_accepted("admin", "host")
def edit_item(id):
    item = archon_view_item(id)
    if (hasattr(item, 'status_code') and item.status_code == 404):
        return "Episode not found"
    shows = frontend_list_shows_without_items()
    shows_sorted = sorted(shows, key=lambda k: k['name'])
    return render_template("item/edit.html", item=item, shows=shows_sorted)
