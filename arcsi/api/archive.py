import json

from flask import jsonify, make_response, request
from arcsi.api import arcsi
from arcsi.model.item import Item


@arcsi.route("/archive", methods=["GET"])
@arcsi.route("/archive/all", methods=["GET"])
def all_archive():
    items = Item.query.all()

    return jsonify(json_list=[item.present_dict for item in items])
