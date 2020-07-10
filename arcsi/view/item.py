import requests

from flask import current_app as app
from flask import redirect, render_template, request, url_for
from flask_login import current_user

from arcsi.view import router


@router.route("/item/all")
def list_items():
    result = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_items"))
    items = result.json()
    return render_template("item/list.html", items=items)


@router.route("/item/add", methods=["GET"])
def add_item():
    if current_user.is_anonymous:
        # TODO error handling
        return redirect(url_for("security.login", _external=True))
    elif not current_user.shows.all():
        # TODO error handling
        return "add new show first"
    return render_template("item/add.html")


@router.route("/item/<id>", methods=["GET"])
def view_item(id):
    relpath = url_for("arcsi.view_item", id=id)
    item = requests.get(app.config["APP_BASE_URL"] + relpath)
    return render_template("item/view.html", item=item.json())


@router.route("/item/<id>/edit", methods=["GET"])
def edit_item(id):
    relpath = url_for("arcsi.edit_item", id=id)
    item = requests.get(app.config["APP_BASE_URL"] + relpath)
    return render_template("item/edit.html", item=item.json())
