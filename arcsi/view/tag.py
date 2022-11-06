import requests

from flask import current_app as app
from flask import render_template, request, url_for
from flask_login import current_user
from flask_security import roles_accepted, roles_required

from arcsi.view import router

@router.route("/tag")
@router.route("/tag/all")
def list_tags():
  tagged = requests.get(app.config["APP_BASE_URL"] + url_for("arcsi.list_tags"))
  tags = tagged.json()
  return render_template("tag/list.html", tags=tags)
