from datetime import datetime, timedelta

from flask import current_app as app
from sqlalchemy import func

from arcsi.api.utils import normalise, process_files

from arcsi.handler.archival import archive
from arcsi.handler.streaming import broadcast_episode, cleanup_show_playlist

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


def handle_files_and_options(request, item, name_occurrence):
    image_file_name = None

    if request.files:
        # overwrites item's play_file_name and broadcast
        item, image_file_name, error, error_message = process_files(
            request,
            item,
            name_occurrence,
            image_file_name,
            error,
            error_message,
        )

    # cleanup previous episode from show's playlist
    if item.live and (error == False):
        cleanup_show_playlist(item.shows[0].playlist_name)

    # archive files if asked
    if item.archive_lahmastore:
        # overwrites item's image_url, archive_lahmastore_canonical_url and archived
        item, error, error_message = archive_files(
            item, image_file_name, error, error_message
        )

    # broadcast episode if asked
    if item.broadcast and (error == False):
        # overwrites item's airing
        item, error, error_message = broadcast_episode(
            item, image_file_name, error, error_message
        )

    return item, error, error_message


def archive_files(item, image_file_name, error, error_message):
    # archive files if asked
    if (error == False) and (item.play_file_name or image_file_name):
        if image_file_name:
            item.image_url = archive(
                norms_show_name=item.shows[0].archive_lahmastore_base_url,
                episode_number=item.number,
                archive_file_name=image_file_name,
            )
            if not item.image_url:
                error = True
                error_message = "ERROR: Image could not be uploaded to storage"
                app.logger.debug(error_message)

        if item.play_file_name:
            item.archive_lahmastore_canonical_url = archive(
                norms_show_name=item.shows[0].archive_lahmastore_base_url,
                episode_number=item.number,
                archive_file_name=item.play_file_name,
            )
            if item.archive_lahmastore_canonical_url:
                # Only set archived if there is audio data otherwise it's live episode
                item.archived = True
            else:  # Upload didn't succeed
                error = True
                error_message = "ERROR: Audio could not be uploaded to storage"
                app.logger.debug(error_message)
    return item, error, error_message
