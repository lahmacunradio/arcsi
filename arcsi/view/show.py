import requests

from flask import current_app as app
from flask import render_template, url_for
from flask_login import current_user
from flask_security import roles_accepted

from arcsi.view import router


@router.route("/show/all")
def list_shows():
    # using auth token protected API in order to demonstrate how it's working in the view context 
    # if not isinstance(current_user._get_current_object(), AnonymousUserMixin):
    if (current_user.has_role("admin")):
        result = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_shows"), headers = {"Authentication-Token": current_user.get_auth_token()})
        shows = result.json()
    else:
        shows = []
    return render_template("show/list.html", shows=shows)


@router.route("/show/add", methods=["GET"])
@roles_accepted("admin", "host")
def add_show():
    return render_template("show/add.html")


@router.route("/show/<id>", methods=["GET"])
def view_show(id):
    if (current_user.has_role("admin")):
        relpath = url_for("arcsi.view_show", id=id)
        show = requests.get(app.config["APP_BASE_URL"] + relpath, headers = {"Authentication-Token": current_user.get_auth_token()})
        show_json = show.json()
    else:
        show_json = []
    return render_template("show/view.html", show=show_json)


@router.route("/show/<id>/edit", methods=["GET"])
@roles_accepted("admin", "host", "guest")
def edit_show(id):
    relpath = url_for("arcsi.view_show", id=id)
    show = requests.get(app.config["APP_BASE_URL"] + relpath, headers = {"Authentication-Token": current_user.get_auth_token()})
    return render_template("show/edit.html", show=show.json())
