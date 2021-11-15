from flask import Blueprint

arcsi = Blueprint("arcsi", __name__, url_prefix="/arcsi")

from .item import *
from .role import *
from .show import *
from .user import *

# TODO add routing here eg
# arcsi.route("/archive", methods=["GET"])(<method_name>)


@arcsi.route("show/<string:show_slug>/archive", methods=["GET"])
def view_show_archive(show_slug):
    show_query = Show.query.filter_by(archive_lahmastore_base_url=show_slug)
    show = show_query.first_or_404()
    if show:
        # filter_date = datetime.today() - timedelta(days=1)
        # airing_date = Item.play_date
        # filter_hour = datetime.now() - timedelta(days=1)
        # airing_hour = show.start
        show_items = show.items.filter(Item.play_date + show.start < datetime.now() - timedelta(days=1)).all()
        return jsonify(many_item_details_schema.dumps(show_items))
    else:
        return make_response("Show not found", 404, headers)


@arcsi.route("show/<string:show_slug>/episode/<string:episode_slug>", methods=["GET"])
def view_episode_archive(show_slug, episode_slug):
    episode_slug += ".mp3"
    item_query = Show.query.filter_by(archive_lahmastore_base_url=show_slug).join(Item, Show.items).first().items.filter_by(play_file_name=episode_slug)
    item = item_query.first_or_404()
    if item:
        return jsonify(item_details_schema.dump(item))
    else:
        return make_response("Item not found", 404, headers)