from flask import Blueprint
from marshmallow import fields, post_load, Schema
from arcsi.model.media import Media

media = Blueprint("media", __name__, url_prefix="/media")


class MediaSimpleSchema(Schema):
    id = fields.Str()
    name = fields.Str(required=True, min=1)
    extension = fields.Str(required=True)
    url = fields.Str(dump_only=True)
    external_storage = fields.Boolean(required=True)
    dimension = fields.Str(dump_only=True)
    created_at = fields.Date(dump_only=True)
    source = fields.Str()
    size = fields.Int(required=True)

    @post_load
    def make_media(self, data, **kwargs):
        return Media(**data)


from .get import *
from .post import *

# part 1.2
# from .put import *

# part 1.2
# media.route(get.endpoint())(get.)
# media.route(post.endpoint)(post.func)
# media.route(put.endpoint)(put.func)
