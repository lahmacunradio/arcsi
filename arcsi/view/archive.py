import requests

from flask import redirect, render_template, request, url_for

from arcsi.view import router


@router.route("/")
def archive():
    result = requests.get("http://" + request.host + url_for("arcsi.all_archive"))
    items = result.json()["json_list"]
    return render_template("archive/list_archive.html", items=items)
