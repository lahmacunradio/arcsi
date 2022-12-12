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
    from_date = date_metadata['from_date']
    given_date = datetime.strptime(from_date, '%Y-%m-%d')
    if (given_date > datetime.today()):
        return make_response("Back to the future?", 418, headers)
    last_days = int(date_metadata['last_days'])
    if (last_days < 0):
        return make_response("Please, be postive!", 400, headers)
    episodes_count = Item.query.filter(
        given_date - timedelta(days=last_days) <= Item.play_date
        ).filter(Item.play_date <= given_date
        ).count()
    ret = {"uploaded_episodes_in_last_%d_days" % (last_days): episodes_count}
    return make_response(jsonify(ret), 200, headers)

@arcsi.route("/data/episodes_uploaded_weekly", methods=["POST"])
@roles_required("guest")
def uploaded_episodes_in_last_x_weeks():
    date_metadata = request.form.to_dict()
    from_date = date_metadata['from_date']
    given_date = datetime.strptime(from_date, '%Y-%m-%d')
    if (given_date > datetime.today()):
        return make_response("Back to the future?", 418, headers)
    last_weeks = int(date_metadata['last_weeks'])
    if (last_weeks < 0):
        return make_response("Please, be postive!", 400, headers)
    episodes_count = Item.query.filter(
        given_date - timedelta(weeks=last_weeks) <= Item.play_date
        ).filter(Item.play_date <= given_date).count()
    ret = {"uploaded_episodes_in_last_%d_weeks" % (last_weeks): episodes_count}
    return make_response(jsonify(ret), 200, headers)