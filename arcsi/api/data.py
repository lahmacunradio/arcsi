from datetime import datetime

from flask import jsonify, make_response, request
from flask_security import roles_required

from . import arcsi
from arcsi.model.item import Item
from arcsi.model.show import Show
from .show import shows_schedule_schema
from .liquidsoap import make_playlist_init_script, make_playlist_schedule_script

headers = {"Content-Type": "application/json"}


@arcsi.route("/data/weekly_schedule", methods=["GET"])
@roles_required("admin")
def weekly_schedule():
    week_number = request.args.get("week", datetime.today().isocalendar().week, type=int)
    abcd_week = week_number % 4
    shows = Show.query.filter(Show.active == True).filter_by(week=abcd_week).order_by(Show.day, Show.start).all()
    shows = shows_schedule_schema.dump(shows)
    playlist_init = make_playlist_init_script(shows)
    playlist_schedule = make_playlist_schedule_script(shows)
    ret = {
        "playlist_init": playlist_init,
        "playlist_schedule": playlist_schedule
    }
    return make_response(jsonify(ret), 200, headers)

@arcsi.route("/data/uploaded_episodes", methods=["POST"])
@roles_required("admin")
def uploaded_episodes():
    date_metadata = request.form.to_dict()
    end_date = date_metadata["end_date"]
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    if end_date > datetime.today():
        return make_response("Back to the future?", 418, headers)

    start_date = date_metadata["start_date"]
    start_date = datetime.strptime(start_date, "%Y-%m-%d")
    if start_date > datetime.today():
        return make_response("Back to the future?", 418, headers)

    if end_date < start_date:
        return make_response("End date should be later than start date!", 400, headers)

    episodes_count = (
        Item.query.filter(start_date <= Item.play_date)
        .filter(Item.play_date <= end_date)
        .count()
    )

    ret = {
        "uploaded_episodes_between_%s_%s"
        % (start_date.date(), end_date.date()): episodes_count
    }
    return make_response(jsonify(ret), 200, headers)
