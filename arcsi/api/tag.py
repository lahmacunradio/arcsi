from marshmallow import fields, post_load, Schema

from arcsi.api import arcsi
from arcsi.model.tag import Tag
from .utils import find_request_params

class TagDetailsSchema(Schema):
    id = fields.Int()
    display_name = fields.Str(required=True, min=3)
    @post_load
    def make_tag(self, data, **kwargs):
        return Tag(**data)

tags_details_schema = TagDetailsSchema()
tags_partial_schema = TagDetailsSchema(partial=True)
many_tags_schema = TagDetailsSchema(many=True)

@arcsi.route("/tag", methods=["GET"])
@arcsi.route("/tag/all", methods=["GET"])
def list_tags():
    tags = Tag.query.all()
    return many_tags_schema.dumps(tags)

@arcsi.route("/tag/<string:base_tag>", methods=["GET"])
def view_tagged(base_tag):
    return base_tag
