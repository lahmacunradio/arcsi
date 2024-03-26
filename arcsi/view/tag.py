import requests

from flask import current_app as app
from flask import render_template, request, url_for
from flask_login import current_user
from flask_security import roles_accepted, roles_required

from arcsi.api import list_tags
from arcsi.view import router

@router.route("/tag")
@router.route("/tag/all")
def list_tags():
  tags = list_tags().json()
  return render_template("tag/list.html", tags=tags)
