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
    iresult = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_items"))
    items = iresult.json()
    uresult = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_users"))
    users = uresult.json()
    sresult = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_shows"))
    shows = sresult.json()
    return render_template(
        "archive/list_archive.html", users=users, shows=shows, items=items
    )
