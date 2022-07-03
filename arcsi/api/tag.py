from marshmallow import fields, post_load, Schema

from arcsi.api import arcsi
from arcsi.model.tag import Tag


class TagDetailsSchema(Schema):
    id = fields.Int()
    display_name = fields.Str(required=True, min=3)
    
    @post_load
    def make_tag(self, data, **kwargs):
        return Tag(**data)

tags_details_schema = TagDetailsSchema()
tags_partial_schema = TagDetailsSchema(partial=True)
many_tags_schema = TagDetailsSchema(many=True)

@arcsi.route("/tags", methods=["GET"])
@arcsi.route("/tags/all", methods=["GET"])
def list_tags():
    tags = Tag.query.all()
    return many_tags_schema.dumps(tags)
