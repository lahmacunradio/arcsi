import requests

from flask import render_template, request, url_for
from flask_login import current_user

from arcsi.view import router


@router.route("/user/all")
def list_users():
    result = requests.get("http://" + request.host + url_for("arcsi.list_users"))
    users = result.json()
    return render_template("user/list.html", users=users)


@router.route("/user/add", methods=["GET"])
def add_user():
    # TODO decide if we just go w/ login or separate creation possible too
    return render_template("user/add.html")


@router.route("/user/edit")
def edit_user():
    user = current_user
    return render_template("user/edit.html", user=user)


@router.route("/user/me")
def view_user():
    user = current_user
    return render_template("user/view.html", user=user)
