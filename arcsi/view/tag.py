from flask import render_template

from arcsi.api import list_tags
from arcsi.view import router


@router.route("/tag")
@router.route("/tag/all")
def list_tags():
    tags = list_tags().json()
    return render_template("tag/list.html", tags=tags)
