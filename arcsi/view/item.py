from flask import render_template
from flask_login import current_user
from flask_security import login_required, roles_accepted


from arcsi.api import archon_view_item, listen_play_file, archon_list_items, shows_minimal_schema
from arcsi.api.utils import get_shows, get_managed_shows
from arcsi.view import router


@router.route("/item/all")
@login_required
def list_items():
    items = archon_list_items()
    return render_template("item/list.html", items=items)


@router.route("/item/add", methods=["GET"])
@roles_accepted("admin", "host")
def add_item():
    if not current_user.has_role("admin") and not current_user.shows.all():
        # TODO error handling
        return "add new show first"

    shows = {}
    if current_user.has_role("admin"):
        shows = shows_minimal_schema.dump(get_shows())
    if current_user.has_role("host"):
        shows = shows_minimal_schema.dump(get_managed_shows(current_user))

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
    
    shows = {}
    if current_user.has_role("admin"):
        shows = shows_minimal_schema.dump(get_shows())
    if current_user.has_role("host"):
        shows = shows_minimal_schema.dump(get_managed_shows(current_user))

    shows_sorted = sorted(shows, key=lambda k: k['name'])
    return render_template("item/edit.html", item=item, shows=shows_sorted)
