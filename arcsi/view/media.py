from flask import current_app as app
from flask import redirect, render_template, request, session, url_for
from flask_login import current_user
from flask_security import login_required, roles_accepted

from arcsi.api.media import MediaSimpleSchema
from arcsi.view import form_api_request, router

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
    response = form_api_request(
        "GET",
        url_for("arcsi.media.all"),
    )
    # TODO if response not ok raise exc
    if response.headers["Content-Type"] == "application/json":
        if current_user.has_role("admin"):
            medium = response.json()
        if current_user.has_role("host"):
            medium = (
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
    response = form_api_request("GET", url_for("arcsi.media.one", id=id))
    if response.headers["Content-Type"] == "application/json":
        one = response.json()
        return render_template("media/one.html", media=one)
    else:
        return "Media not found"


@router.route("/media/<id>/edit")
@roles_accepted("admin", "host")
def edit_media(id):
    response = form_api_request("GET", url_for("arcsi.media.one", id=id))
    if response.headers["Content-Type"] == "application/json":
        one = response.json()
        return render_template("media/edit.html", media=one)
    else:
        return "Media not found"
