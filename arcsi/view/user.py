from flask import render_template
from flask_login import current_user
from flask_security import login_required, roles_required

from arcsi.api import list_users
from arcsi.view import router


@router.route("/user/all")
@roles_required("admin")
def view_list_users():
    users = list_users()
    return render_template("user/list.html", users=users)


@router.route("/user/add", methods=["GET"])
@roles_required("admin")
def add_user():
    # TODO decide if we just go w/ login or separate creation possible too
    return render_template("user/add.html")


@router.route("/user/edit")
@login_required
def edit_user():
    user = current_user
    return render_template("user/edit.html", user=user)


@router.route("/user/me")
@login_required
def view_user():
    user = current_user
    return render_template("user/view.html", user=user)
