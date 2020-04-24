from flask import render_template

from arcsi.view import router


@router.route("/add", methods=["GET"])
def add():
    return render_template("add/add.html")
