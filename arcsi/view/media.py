from flask import render_template
from flask_login import current_user
from flask_security import login_required, roles_accepted

from arcsi.view import request_api, router


@router.route("/media/all")
@router.route("/media/list")
@router.route("/media")
@login_required
def list_medias():
    medias = {}
    response = request_api(
        "media",
        endpoint="all",
    )
    if response.ok:
        if current_user.has_role("admin"):
            medias = response.json
        if current_user.has_role("host"):
            medias = response.json  # create api endpoint scoped to user owned media
        return render_template("media/list.html", medias=medias)
    else:
        return "No media found."


@router.route("/media/new")
@roles_accepted("admin", "host")
def add_media():
    return render_template("media/new.html")


@router.route("/media/<str:id>")
@login_required
def view_media(id):
    response = request_api("media", id=id)
    if response.ok:
        return render_template("media/one.html", media=response.json)
    else:
        return "Media not found"


@router.route("/media/<id>/edit")
@roles_accepted("admin", "host")
def edit_media(id):
    response = request_api("media", id=id)
    if response.ok:
        return render_template("media/edit.html", media=response.json)
    else:
        return "Media not found"
