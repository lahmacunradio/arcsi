import json
import os

from flask import flash, jsonify, make_response, request, url_for
from flask import current_app as app
from marshmallow import fields, post_load, Schema, ValidationError

from arcsi.api import arcsi
from arcsi.model import db
from arcsi.model.show import Show
from arcsi.model.user import User


class UserDetailsSchema(Schema):
    id = fields.Int()
    active = fields.Boolean(required=True)
    butt_user = fields.Str()
    butt_pw = fields.Str()
    email = fields.Str()
    name = fields.Str(required=True)
    password = fields.Str(required=True)
    shows = fields.List(
        fields.Nested("ShowDetailsSchema", only=("id", "name"),), dump_only=True
    )
    # TODO roles
    roles = fields.Str()

    @post_load
    def make_user(self, data, **kwargs):
        # data["shows"] = dict_to_obj(dict_name=data["shows"], table=Show)
        return User(**data)


user_details_schema = UserDetailsSchema()
user_details_partial_schema = UserDetailsSchema(partial=True)
many_user_details_schema = UserDetailsSchema(many=True)

headers = {"Content-Type": "application/json"}


@arcsi.route("/users", methods=["GET"])
@arcsi.route("/users/all", methods=["GET"])
def list_users():
    users = User.query.all()
    return many_user_details_schema.dumps(users)


@arcsi.route("/user/<id>", methods=["GET"])
def view_user(id):
    user_query = User.query.filter_by(id=id)
    user = user_query.first_or_404()
    if user:
        return jsonify(user_details_schema.dump(user))
    else:
        return make_response(jsonify("Could not find user", 404, headers))
