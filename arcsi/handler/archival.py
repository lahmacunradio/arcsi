import boto3
import os

from botocore.exceptions import ClientError
from flask import current_app as app

from arcsi.api.utils import media_path, normalise

from arcsi.model.show import Show


class S3Config(object):
    def __init__(self):
        self.config = {
            "region": app.config["ARCHIVE_REGION"],  # region
            "host": app.config["ARCHIVE_HOST_BASE_URL"],  # origin
            "api_key": app.config["ARCHIVE_API_KEY"],
            "secret_key": app.config["ARCHIVE_SECRET_KEY"],
        }

    def get_client(self):
        sess = boto3.session.Session()
        return sess.client(
            "s3",
            region_name=self.config["region"],
            endpoint_url=self.config["host"],
            aws_access_key_id=self.config["api_key"],
            aws_secret_access_key=self.config["secret_key"],
        )


class DoArchive(S3Config):
    def __init__(self):
        super().__init__()
        self.config.update(
            {
                "endpoint": app.config["ARCHIVE_ENDPOINT"],  # public
            }
        )

    # Should we have one session for class instance or one each for each method called?

    def upload(self, media_file, show_name, number):
        file_name = os.path.basename(media_file)

        cli = self.get_client()
        try:
            cli.upload_file(
                media_file,
                show_name,
                "{}/{}".format(number, file_name),
                ExtraArgs={"ACL": "public-read"},
            )
        except ClientError:
            return False
        return "{}/{}".format(number, file_name)

    def download(self, show_name, file_name):
        return "{}/{}/{}".format(self.config["endpoint"], show_name, file_name)


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


def archive(norms_show_name, episode_number, archive_file_name):
    archive_file_path = media_path(
        norms_show_name, str(episode_number), archive_file_name
    )
    do = DoArchive()
    archive_url = do.upload(archive_file_path, norms_show_name, episode_number)
    return archive_url


def get_audio(item):
    do = DoArchive()
    return do.download(
        item.shows[0].archive_lahmastore_base_url, item.archive_lahmastore_canonical_url
    )


def get_show_cover(show):
    do = DoArchive()
    if show.cover_image_url:
        show.cover_image_url = do.download(
            show.archive_lahmastore_base_url, show.cover_image_url
        )
    return show


def get_show_cover_json(show_json):
    do = DoArchive()
    if show_json["cover_image_url"]:
        show_json["cover_image_url"] = do.download(
            show_json["archive_lahmastore_base_url"], show_json["cover_image_url"]
        )
    return show_json


def get_shows_with_cover():
    do = DoArchive()
    shows = Show.query.all()
    for show in shows:
        if show.cover_image_url:
            show.cover_image_url = do.download(
                show.archive_lahmastore_base_url, show.cover_image_url
            )
    return shows


def get_item_fields(item):
    do = DoArchive()
    if item.image_url:
        item.image_url = do.download(
            item.shows[0].archive_lahmastore_base_url, item.image_url
        )
    item.name_slug = normalise(item.name)
    return item


def get_item_fields_json(item_json, show_json):
    do = DoArchive()
    item_json["image_url"] = do.download(
        show_json["archive_lahmastore_base_url"], item_json["image_url"]
    )
    item_json["name_slug"] = normalise(item_json["name"])


def get_show_items(show, items, latest):
    do = DoArchive()
    if latest:
        items = items[0]
        items["image_url"] = do.download(
            show.archive_lahmastore_base_url, items["image_url"]
        )
        items["name_slug"] = normalise(items["name"])
        return items
    else:
        for item in items:
            item["image_url"] = do.download(
                show.archive_lahmastore_base_url, item["image_url"]
            )
            item["name_slug"] = normalise(item["name"])
        return items
