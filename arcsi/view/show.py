from flask import render_template
from flask_login import current_user
from flask_security import login_required, roles_accepted, roles_required

from arcsi.api import archon_view_show, archon_shows_schema
from arcsi.api.utils import (
    get_shows,
    get_managed_shows,
    get_managed_show,
)
from arcsi.handler.upload import AzuraArchive
from arcsi.view import router


@router.route("/show/all")
@login_required
def list_shows():
    shows = {}
    if current_user.has_role("admin"):
        shows = archon_shows_schema.dump(get_shows())
    if current_user.has_role("host"):
        shows = archon_shows_schema.dump(get_managed_shows(current_user))
    return render_template("show/list.html", shows=shows)


@router.route("/show/add", methods=["GET"])
@roles_required("admin")
def add_show():
    return render_template("show/add.html")


@router.route("/show/<id>", methods=["GET"])
@login_required
def view_show(id):
    show = archon_view_show(id)
    if hasattr(show, "status_code") and show.status_code == 404:
        return "Show not found"
    az = AzuraArchive(
        None,
        None,
        None,
        None,
        None,
        show.get("playlist_name"),
    )
    existing_playlist = az.find_playlist_id()
    empty_playlist = True
    if existing_playlist:
        empty_playlist = az.empty_playlist()
    return render_template(
        "show/view.html",
        show=show,
        existing_playlist=existing_playlist,
        empty_playlist=empty_playlist,
    )


@router.route("/show/<id>/edit", methods=["GET"])
@roles_accepted("admin", "host")
def edit_show(id):
    show = archon_view_show(id)
    if hasattr(show, "status_code") and show.status_code == 404:
        return "Show not found"
    if not current_user.has_role("admin") and not get_managed_show(current_user, id):
        return "You don't have access to edit this show!"
    return render_template("show/edit.html", show=show)
