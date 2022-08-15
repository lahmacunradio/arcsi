import requests

from flask import current_app as app
from flask import render_template, request, url_for, jsonify
from flask_security import login_required
from flask_login import current_user

from arcsi.model import guard
from arcsi.view import router


@router.route("/")
# Flask-Security
# @login_required
def archive():
    return render_template(
        "archive/list_archive.html"
    )

@router.route("/api_key_admin")
@login_required
def api_key_admin():
    user=current_user
    token=user.get_auth_token()
    ret = {"access_token": token}
    return (jsonify(ret), 200)
