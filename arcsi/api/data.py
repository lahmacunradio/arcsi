from datetime import datetime, timedelta

from flask import jsonify, make_response, request
from flask_security import roles_required

from . import arcsi
from arcsi.model.item import Item

headers = {"Content-Type": "application/json"}

@arcsi.route("/data/episodes_uploaded_daily", methods=["POST"])
@roles_required("guest")
def uploaded_episodes_in_last_x_days():
    date_metadata = request.form.to_dict()
    end_date = date_metadata['end_date']
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    if (end_date > datetime.today()):
        return make_response("Back to the future?", 418, headers)

    days = int(date_metadata['days'])
    if (days < 1):
        return make_response("Please, be postive!", 400, headers)

    start_date = end_date - timedelta(days=days)
    episodes_count = Item.query.filter(
        start_date < Item.play_date
        ).filter(Item.play_date <= end_date).count()

    ret = {"uploaded_episodes_between_%s_%s" % (start_date.date(), end_date.date()): episodes_count}
    return make_response(jsonify(ret), 200, headers)

@arcsi.route("/data/episodes_uploaded_weekly", methods=["POST"])
@roles_required("guest")
def uploaded_episodes_in_last_x_weeks():
    date_metadata = request.form.to_dict()
    end_date = date_metadata['end_date']
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    if (end_date > datetime.today()):
        return make_response("Back to the future?", 418, headers)

    weeks = int(date_metadata['weeks'])
    if (weeks < 1):
        return make_response("Please, be postive!", 400, headers)

    start_date = end_date - timedelta(weeks=weeks)
    episodes_count = Item.query.filter(
        start_date < Item.play_date
        ).filter(Item.play_date <= end_date).count()

    ret = {"uploaded_episodes_between_%s_%s" % (start_date.date(), end_date.date()): episodes_count}
    return make_response(jsonify(ret), 200, headers)