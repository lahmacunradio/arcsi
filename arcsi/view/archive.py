from flask import render_template

from arcsi.view import router


@router.route("/")
# Flask-Security
# @login_required
def archive():
    return render_template("archive/list_archive.html")


@router.route("/faq")
# Flask-Security
# @login_required
def faq():
    return render_template("archive/faq.html")
