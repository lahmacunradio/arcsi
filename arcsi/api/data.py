from datetime import datetime, timedelta

from flask import jsonify, make_response, request
from flask_security import roles_required

from . import arcsi
from arcsi.model.item import Item

headers = {"Content-Type": "application/json"}

@arcsi.route("/data/episodes_uploaded", methods=["POST"])
@roles_required("guest")
def uploaded_episodes():
    date_metadata = request.form.to_dict()
    end_date = date_metadata['end_date']
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    if (end_date > datetime.today()):
        return make_response("Back to the future?", 418, headers)
    
    start_date = date_metadata['start_date']
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    if (start_date > datetime.today()):
        return make_response("Back to the future?", 418, headers)

    if (end_date < start_date):
        return make_response("End date should be later than start date!", 400, headers)

    episodes_count = Item.query.filter(
        start_date <= Item.play_date
        ).filter(Item.play_date <= end_date).count()

    ret = {"uploaded_episodes_between_%s_%s" % (start_date.date(), end_date.date()): episodes_count}
    return make_response(jsonify(ret), 200, headers)