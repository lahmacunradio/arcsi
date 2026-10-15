from datetime import datetime, timedelta

from flask import current_app as app
from sqlalchemy import func

from arcsi.api.utils import normalise

from arcsi.model.item import Item
from arcsi.model.show import Show
from arcsi.model.tag import Tag

from arcsi.utils.show import get_managed_shows


def get_items():
    items = Item.query.all()
    return items


def search_items(param):
    return (
        Item.query.filter(
            func.lower(Item.name).contains(func.lower(param))
            | func.lower(Item.description).contains(func.lower(param))
        )
        .filter(Item.play_date < datetime.today() - timedelta(days=1))
        .filter(Item.archived == True)
    )


def search_show_items(param):
    return (
        Item.query.join(Item.shows)
        .filter(func.lower(Show.name).contains(func.lower(param)))
        .filter(Item.play_date < datetime.today() - timedelta(days=1))
        .filter(Item.archived == True)
    )


def search_tag_items(param):
    return (
        Item.query.join(Item.tags)
        .filter(func.lower(Tag.clean_name).contains(normalise(param)))
        .filter(Item.play_date < datetime.today() - timedelta(days=1))
        .filter(Item.archived == True)
    )


def search_items_by_tag(param):
    return (
        Item.query.join(Item.tags)
        .filter(func.lower(Tag.clean_name) == (func.lower(param)))
        .filter(Item.play_date < datetime.today() - timedelta(days=1))
        .filter(Item.archived == True)
    )


def get_managed_items(user):
    managed_shows = get_managed_shows(user)
    managed_items = []
    for managed_show in managed_shows:
        managed_items_for_current_show = Item.query.filter(
            Item.shows.contains(managed_show)
        ).all()
        managed_items.extend(managed_items_for_current_show)
    return managed_items


def show_item_duplications_number(item):
    existing_items = Show.query.filter(Show.id == item.shows[0].id).first().items
    existing_items_with_same_name = existing_items.filter_by(name=item.name)
    name_occurrence = existing_items_with_same_name.count()
    app.logger.error("Name_occurence (duplicate detection): {}".format(name_occurrence))
    return name_occurrence
