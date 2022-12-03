from datetime import date, timedelta

from flask import jsonify, make_response, request
from flask_security import auth_token_required

from . import arcsi
from arcsi.model.item import Item

headers = {"Content-Type": "application/json"}

@arcsi.route("/data/episodes_uploaded_daily", methods=["GET"])
@auth_token_required
def get_uploaded_episodes_in_last_x_days():
    year = request.args.get('year', date.today().year(), type=int)
    if (year > date.today().year()):
        return make_response("Back to the future?", 418, headers)
    month = request.args.get('month', date.today().month(), type=int)
    if (year == date.today().year() and month > date.today().month()):
        return make_response("Back to the future?", 418, headers)
    day = request.args.get('day', date.today().day(), type=int)
    if (year == date.today().year() and month == date.today().month() and day > date.today().day()):
        return make_response("Back to the future?", 418, headers)
    given_date = date(year, month, day)
    last_days = request.args.get('last_days', 7, type=int)
    episodes_count = Item.query.filter(
        given_date - timedelta(days=last_days) <= Item.play_date
        ).filter(Item.play_date <= date.today()
        ).filter(Item.archived == True).count()
    ret = {"uploaded_episodes_in_last_%d_days" % (last_days): episodes_count}
    return make_response(jsonify(ret), 200, headers)

@arcsi.route("/data/episodes_uploaded_weekly", methods=["GET"])
@auth_token_required
def get_uploaded_episodes_in_last_x_weeks():
    year = request.args.get('year', date.today().year(), type=int)
    if (year > date.today().year()):
        return make_response("Back to the future?", 418, headers)
    month = request.args.get('month', date.today().month(), type=int)
    if (year == date.today().year() and month > date.today().month()):
        return make_response("Back to the future?", 418, headers)
    day = request.args.get('day', date.today().day(), type=int)
    if (year == date.today().year() and month == date.today().month() and day > date.today().day()):
        return make_response("Back to the future?", 418, headers)
    given_date = date(year, month, day)
    last_weeks = request.args.get('last_weeks', 1, type=int)
    episodes_count = Item.query.filter(
        given_date - timedelta(weeks=last_weeks) <= Item.play_date
        ).filter(Item.play_date <= date.today()
        ).filter(Item.archived == True).count()
    ret = {"uploaded_episodes_in_last_%d_weeks" % (last_weeks): episodes_count}
    return make_response(jsonify(ret), 200, headers)