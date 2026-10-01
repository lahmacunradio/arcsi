import boto3
import os

from botocore.exceptions import ClientError
from flask import current_app as app


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
        super.__init__()
        self.config = {
            "endpoint": app.config["ARCHIVE_ENDPOINT"],  # public
        }

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
