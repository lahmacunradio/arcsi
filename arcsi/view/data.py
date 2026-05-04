from flask import render_template
from flask_security import roles_required

from arcsi.view import router


@router.route("/data")
@roles_required("admin")
def view_data():
    return render_template("data/view.html")


@router.route("/data/uploaded_episodes")
@roles_required("admin")
def uploaded_episodes():
    return render_template("data/uploaded_episodes.html")
