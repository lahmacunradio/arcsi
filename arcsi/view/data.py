import requests

from flask import current_app as app
from flask import render_template, request, url_for
from flask_login import current_user
from flask_security import login_required, roles_required

from arcsi.view import router

@router.route("/data")
@login_required
def view_data():
    return render_template("data/view.html")

@router.route("/data/latest_uploaded_episodes_daily")
@login_required
def uploaded_episodes_in_last_x_days():
    return render_template("data/uploaded_episodes_daily.html")

@router.route("/data/latest_uploaded_episodes_weekly")
@login_required
def uploaded_episodes_in_last_x_weeks():
    return render_template("data/uploaded_episodes_weekly.html")