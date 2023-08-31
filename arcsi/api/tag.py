from flask import make_response
from flask_security import auth_token_required
from marshmallow import fields, post_load, Schema

from arcsi.api import arcsi
from arcsi.model.tag import Tag
from .utils import find_request_params, normalise

class TagDetailsSchema(Schema):
    id = fields.Int()
    display_name = fields.Str(required=True, min=3)
    clean_name = fields.Str(dump_only=True)
    icon = fields.Str(dump_only=True)
    items = fields.Nested("ItemDetailsSchema", many=True, only=("id", "name", "name_slug", "description", "image_url", "play_date"), dump_only=True)
    shows = fields.Nested("ShowDetailsSchema", many=True, only=("id", "name", "archive_lahmastore_base_url", "description", "cover_image_url"), dump_only=True)

    # TODO -- Tag count
    
    @post_load
    def make_tag(self, data, **kwargs):
        return Tag(**data)

tags_details_schema = TagDetailsSchema()
many_tags_schema = TagDetailsSchema(many=True)

headers = {"Content-Type": "application/json"}

@arcsi.route("/tag", methods=["GET"])
@arcsi.route("/tag/all", methods=["GET"])
@auth_token_required
def list_tags():
    tags = Tag.query.all()
    return make_response(many_tags_schema.dumps(tags), 200 , headers,)

@arcsi.route("/tag/<string:clean_tag>", methods=["GET"])
@auth_token_required
def view_tagged(clean_tag):
    tag = Tag.query.filter_by(clean_name=clean_tag).first_or_404()
    if tag:
        for item in tag.items:
            item.name_slug=normalise(item.name)    
        return make_response(tags_details_schema.dumps(tag), 200, headers,)
