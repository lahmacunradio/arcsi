from flask import render_template

from arcsi.view import router


@router.route("/")
def archive():
    return render_template("archive/list_archive.html")


@router.route("/faq")
def faq():
    return render_template("archive/faq.html")
