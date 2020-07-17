import requests

from flask import current_app as app
from flask import render_template, request, url_for
from flask_login import current_user
from flask_security import roles_accepted

from arcsi.view import router


@router.route("/item/all")
def list_items():
    result = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_items"))
    items = result.json()
    return render_template("item/list.html", items=items)


@router.route("/item/add", methods=["GET"])
@roles_accepted("admin", "host")
def add_item():
    shows = {}

    if not current_user.has_role("admin") and not current_user.shows.all():
        # TODO error handling
        return "add new show first"

    if current_user.has_role("admin"):
        result = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_shows"))
        shows = result.json()

    return render_template("item/add.html", shows=shows)


@router.route("/item/<id>", methods=["GET"])
def view_item(id):
    relpath = url_for("arcsi.view_item", id=id)
    item = requests.get(app.config["APP_BASE_URL"] + relpath)
    return render_template("item/view.html", item=item.json())


@router.route("/item/<id>/edit", methods=["GET"])
def edit_item(id):
    relpath = url_for("arcsi.edit_item", id=id)
    item = requests.get(app.config["APP_BASE_URL"] + relpath)

    shows = {}
    if current_user.has_role("admin"):
        result = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_shows"))
        shows = result.json()

    return render_template("item/edit.html", item=item.json(), shows=shows)
