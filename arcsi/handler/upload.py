"""
***TODO***
[] -- Logger
"""
import os
import queue
import threading

import boto3
from botocore.exceptions import ClientError


class DoArchive(object):
    def __init__(self, *config):
        # eventually move this to app config if we only have one endpoint
        # otherwise if we want to support multiple uploads (eg. DO & Mixcloud) we need dynamic config
        if config:
            self.config = config
        else:
            self.config = {
                "region": "",  # digitalocean region
                "host": "",  # digitalocean droplet IP
                "api_key": "",  # digitalocean access key see API_KEYS
                "secret_key": "",  # digitalocean secret key see API_KEYS
                "space": "",  # digitalocean upload space (eg. folder)
            }

    def upload(self, upload_file):
        self.file = upload_file
        self.filename = os.path.basename(upload_file)

        sess = boto3.session.Session()
        cli = sess.client(
            "s3",
            region_name=self.config["region"],
            endpoint_url=self.config["host"],
            aws_access_key_id=self.config["api_key"],
            aws_secret_access_key=self.config["secret_key"],
        )
        try:
            res = cli.upload_file(self.file, self.config["space"], self.filename)
        except ClientError:
            return False
        # https://github.com/boto/boto3/issues/169
        config = Config(signature_version=botocore.UNSIGNED)
        config.signature_version = botocore.UNSIGNED
        return boto3.client(
            self.config["region"], config=config
        ).generate_presigned_url(
            "get_object", Params={"Bucket": self.config["space"], "Key": self.filename}
        )
        # How about expiration date? `ExpiresIn=0` tops out at 7 days maybe? We have GET API anyway but we should still have another look

    # STUB lets see what the final architecture would look like
    def batch_upload(self):
        upload_queue = UploadQueue(100)
        # get list of non uploaded items from arcsidb
        threading.Thread(target=upload, args=(upload_queue,)).start()


class UploadQueue(queue.Queue):
    def __init__(self):
        self.chunk_size = 1024

    def write(self, data):
        if data:
            self.put(data)

    def __iter__(self):
        return iter(self.get, None)

    def close(self):
        self.put(None)
