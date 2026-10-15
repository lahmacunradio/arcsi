from datetime import datetime, timedelta
from sqlalchemy import func

from arcsi.api.utils import save_file

from arcsi.handler.archival import (
    archive,
    get_show_cover_json,
    get_item_fields_json,
    get_show_items,
)

from arcsi.model.show import Show
from arcsi.model.tag import Tag


def get_shows():
    shows = Show.query.all()
    return shows


def get_active_shows_on_given_week(request):
    week = request.args.get("week", 1, type=int)
    abcd_week = week % 4
    return Show.query.filter(Show.active == True).filter(Show.week.any(abcd_week))


def get_managed_show(user, id):
    managed_show = (
        Show.query.filter(Show.users.contains(user)).filter(Show.id == id).all()
    )
    return managed_show


def get_managed_shows(user):
    managed_shows = Show.query.filter(Show.users.contains(user)).all()
    return managed_shows


def get_shows_with_latest_item(shows, schema):
    shows_json = schema.dump(shows)
    # iterate through shows
    for show_json in shows_json:
        get_show_cover_json(show_json)
        if show_json["items"]:
            latest_item_found = False
            # iterate through show's items
            for item_json in show_json["items"]:
                # search for the first one which is archived & already aired
                if (
                    latest_item_found == False
                    and item_json["archived"] == True
                    and (
                        (
                            datetime.strptime(item_json["play_date"], "%Y-%m-%d")
                            + timedelta(days=1)
                        )
                        < datetime.today()
                    )
                ):
                    latest_item_found = True
                    get_item_fields_json(item_json, show_json)
                    show_json["items"] = item_json
            # if there is no archived show return empty array
            if latest_item_found == False:
                show_json["items"] = []
    return shows_json


def filter_show_items(show, items, archived, latest):
    items = sorted(items, key=lambda x: x["play_date"], reverse=True)
    if archived:
        already_aired_items = [
            show_item
            for show_item in items
            if (
                show_item.get("archived")
                & (
                    datetime.strptime(show_item.get("play_date"), "%Y-%m-%d")
                    + timedelta(days=1)
                    < datetime.today()
                )
            )
        ]
        if 0 < len(already_aired_items):
            return get_show_items(show, already_aired_items, latest)
        else:
            return []
    else:
        return get_show_items(show, items, latest)


def search_shows_by_tag(param):
    return Show.query.join(Show.tags).filter(
        func.lower(Tag.clean_name) == (func.lower(param))
    )


def save_and_archive_file(request, show):
    if request.files:
        if request.files["image_file"]:
            cover_image_name = save_file(
                norms_show_name=show.archive_lahmastore_base_url,
                episode_number=0,
                archive_file=request.files["image_file"],
                archive_file_name=(show.name, "cover"),
            )
            if cover_image_name:
                show.cover_image_url = archive(
                    norms_show_name=show.archive_lahmastore_base_url,
                    episode_number=0,
                    archive_file_name=cover_image_name,
                )
    return show
