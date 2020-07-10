import requests

from flask import render_template, request, url_for

from arcsi.view import router


@router.route("/show/all")
def list_shows():
    result = requests.get("http://" + request.host + url_for("arcsi.list_shows"))
    shows = result.json()
    return render_template("show/list.html", shows=shows)


@router.route("/show/add", methods=["GET"])
def add_show():
    return render_template("show/add.html")


@router.route("/show/<id>", methods=["GET"])
def view_show(id):
    relpath = url_for("arcsi.view_show", id=id)
    print(request.host)
    print(request.host_url)
    show = requests.get("http://" + request.host + relpath)
    return render_template("show/view.html", show=show.json())


@router.route("/show/<id>/edit", methods=["GET"])
def edit_show(id):
    relpath = url_for("arcsi.edit_show", id=id)
    show = requests.get("http://" + request.host + relpath)
    return render_template("show/edit.html", show=show.json())
