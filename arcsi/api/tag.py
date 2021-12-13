from flask import make_response
from marshmallow import fields, post_load, Schema

from arcsi.api import arcsi
from arcsi.model.tag import Tag
from .utils import find_request_params

class TagDetailsSchema(Schema):
    id = fields.Int()
    display_name = fields.Str(required=True, min=3)
    clean_name = fields.Str(dump_only=True)
    icon = fields.Str(dump_only=True)
    items = fields.Nested("ItemDetailsSchema", many=True, only=("id", "name"), dump_only=True)
    shows = fields.Nested("ShowDetailsSchema", many=True, only=("id", "name"), dump_only=True)

    # TODO -- Tag count
    
    @post_load
    def make_tag(self, data, **kwargs):
        return Tag(**data)

tags_details_schema = TagDetailsSchema()
many_tags_schema = TagDetailsSchema(many=True)

headers = {"Content-Type": "application/json"}

@arcsi.route("/tag", methods=["GET"])
@arcsi.route("/tag/all", methods=["GET"])
def list_tags():
    tags = Tag.query.all()
    return make_response(many_tags_schema.dumps(tags), 200 , headers,)

@arcsi.route("/tag/<string:clean_tag>", methods=["GET"])
def view_tagged(clean_tag):
    tag_items = Tag.query.filter_by(clean_name=clean_tag).first_or_404()
    if tag_items:
       return make_response(tags_details_schema.dumps(tag_items), 200, headers,)
