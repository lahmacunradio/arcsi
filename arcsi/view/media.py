from requests import request as rq

from flask import current_app as app
from flask import redirect, render_template, request, session, url_for
from flask_login import current_user
from flask_security import login_required, roles_accepted

from arcsi.api.media import MediaSimpleSchema
from arcsi.view import router

headers = {"Content-Type": "application/json"}

schema_lists = MediaSimpleSchema(
    many=True,
    only=(
        "id",
        "tie",
        "binding",
        "size",
        "name",
        "extension",
        "dimension",
        "url",
    ),
)

schema_one = MediaSimpleSchema(
    many=False,
    only=(
        "id",
        "tie",
        "binding",
        "size",
        "name",
        "url",
        "extension",
        "dimension",
    ),
)


@router.route("/media/all")
@router.route("/media/list")
@router.route("/media")
@login_required
def list_media():
    medium = {}

    response = rq(
        "GET",
        "http://web:5666" + url_for("arcsi.media.all"),
        headers=headers,
        cookies={"session": request.cookies["session"]},
    )
    if response.headers["Content-Type"] == "application/json":
        if current_user.has_role("admin"):
            medium = schema_lists.load(response.json())
        if current_user.has_role("host"):
            medium = schema_lists.load(
                response.json()
            )  # TODO create api endpoint scoped to user owned media
        return render_template("media/list.html", medium=medium)
    else:
        return "No media found."


@router.route("/media/new")
@roles_accepted("admin", "host")
def add_media():
    return render_template("media/new.html")


@router.route("/media/<id>")
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
