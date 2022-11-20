from datetime import datetime, timedelta

from flask import jsonify, make_response, request, redirect
from flask_security import auth_token_required

from . import arcsi
from arcsi.model.item import Item

headers = {"Content-Type": "application/json"}

@arcsi.route("/data/items_uploaded", methods=["GET"])
@auth_token_required
def get_uploaded_items_in_last_x_days():
    days = request.args.get('days', 7, type=int)
    item_count = Item.query.filter(
        datetime.today() - timedelta(days=days) <= Item.play_date
        ).filter(Item.play_date <= datetime.today()
        ).filter(Item.archived == True).count()
    ret = {"item_count": item_count}
    return make_response(jsonify(ret), 200, headers)