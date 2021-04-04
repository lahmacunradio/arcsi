import requests

from flask import current_app as app
from flask import render_template, request, url_for
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
