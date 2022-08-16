import requests

from flask import current_app as app
from flask import render_template, request, url_for, jsonify
from flask_security import login_required
from flask_login import current_user

from arcsi.view import router


@router.route("/")
# Flask-Security
# @login_required
def archive():
    return render_template(
        "archive/list_archive.html"
    )

# draft, just for testing
@router.route("/api_token_admin")
@login_required
def api_token_admin():
    token=current_user.get_auth_token()
    ret = {"access_token": token}
    return (jsonify(ret), 200)
# draft, just for testing
