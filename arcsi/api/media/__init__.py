from b64uuid import B64UUID
from flask import Blueprint
from marshmallow import fields, post_dump, post_load, pre_dump, pre_load, Schema
from arcsi.model.media import Media


media = Blueprint("media", __name__, url_prefix="/media")


## TODO create option http request for media that can check if file is valid to upload
# set extension and size to required in that case
class MediaSimpleSchema(Schema):
    id = fields.Str()
    name = fields.Str(required=True, min=1)
    extension = fields.Str()
    url = fields.Url(dump_only=True)
    external_storage = fields.Boolean(required=True)
    dimension = fields.Str(dump_only=True)
    created_at = fields.Date(dump_only=True)
    # allow uploading before assigning to show
    # Keep tie and binding data optional
    tie = fields.Str()
    binding = fields.Str()
    size = fields.Int()

    """
    This decorated function runs to do a conversion on media ID's during interfacing with API calls.
    When serialising objects to reduce payload and allow simpler human interaction, turn Media ID into b64.
    """

    @post_dump
    def make_front_face(self, data, **kwargs):
        data["id"] = B64UUID(data["id"]).string
        return data

    """
    This decorated function runs to do a conversion on media ID's during interfacing with API calls.
    When deserialising request payload we change from short to long ID's for any further operations.
    """

    @pre_load
    def make_back_face(self, data, **kwargs):
        # ID is created after POST request to endpoint /new
        # Guard against those requests throwing Exceptions
        if data.get("id"):  # GET PUT etc.
            data["id"] = str(B64UUID(data["id"]).uuid)
        return data

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
