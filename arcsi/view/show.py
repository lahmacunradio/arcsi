from flask import render_template
from flask_login import current_user
from flask_security import login_required, roles_accepted, roles_required

from arcsi.api import archon_list_shows, archon_view_show
from arcsi.view import router


@router.route("/show/all")
@login_required
def list_shows():
    shows = archon_list_shows()
    return render_template("show/list.html", shows=shows)


@router.route("/show/add", methods=["GET"])
@roles_required("admin")
def add_show():
    return render_template("show/add.html")


@router.route("/show/<id>", methods=["GET"])
@login_required
def view_show(id):
    show = archon_view_show(id)
    if (hasattr(show, 'status_code') and show.status_code == 404):
        return "Show not found"
    return render_template("show/view.html", show=show)


@router.route("/show/<id>/edit", methods=["GET"])
@roles_accepted("admin", "host")
def edit_show(id):
    show = archon_view_show(id)
    if (hasattr(show, 'status_code') and show.status_code == 404):
        return "Show not found"
    if (not current_user.has_role("admin") and not next(filter(lambda show: show['id']==id, current_user.shows))):
        return "You don't have access to edit this show!"
    return render_template("show/edit.html", show=show)
