"""
***TODO***
[] -- Logger
"""

import boto3
import botocore
import math
import os
import queue
import requests
import threading
import time

from base64 import b64encode
from botocore.exceptions import ClientError
from botocore.config import Config

from flask import current_app as app

from mutagen.id3 import ID3, ID3NoHeaderError, APIC, TIT2, TPE1
from mutagen.mp3 import MP3


class DoArchive(object):
    def __init__(self):
        self.config = {
            "region": app.config["ARCHIVE_REGION"],  # digitalocean region
            "host": app.config["ARCHIVE_HOST_BASE_URL"],  # digitalocean droplet IP
            "api_key": app.config[
                "ARCHIVE_API_KEY"
            ],  # digitalocean access key see API_KEYS
            "secret_key": app.config[
                "ARCHIVE_SECRET_KEY"
            ],  # digitalocean secret key see API_KEYS
            "space": "",  # digitalocean upload space (eg. bucket)
        }

    # Should we have one session for class instance or one each for each method called?

    def upload(self, upload_file, space, number):
        self.file = upload_file
        self.filename = os.path.basename(upload_file)
        self.config["space"] = space

        sess = boto3.session.Session()
        cli = sess.client(
            "s3",
            region_name=self.config["region"],
            endpoint_url=self.config["host"],
            aws_access_key_id=self.config["api_key"],
            aws_secret_access_key=self.config["secret_key"],
        )
        try:
            res = cli.upload_file(
                self.file, self.config["space"], "{}/{}".format(number, self.filename)
            )
        except ClientError:
            return False
        return "{}/{}".format(number, self.filename)

    def download(self, space, path):
        self.config["space"] = space

        sess = boto3.session.Session()
        cli = sess.client(
            "s3",
            region_name=self.config["region"],
            endpoint_url=self.config["host"],
            aws_access_key_id=self.config["api_key"],
            aws_secret_access_key=self.config["secret_key"],
        )

        self.presigned = cli.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.config["space"], "Key": "{}".format(path),},
        )
        return self.presigned

    # TODO cant do this w/o db entry but then its perhaps easier to set expiry time in db
    def valid_presigned(self, url):
        req = requests.post(self.presigned)
        if req.ok:
            return True
        return False

    # TODO STUB lets see what the final architecture would look like
    def batch_upload(self):
        upload_queue = UploadQueue(100)
        # get list of non uploaded items from arcsidb
        threading.Thread(target=upload, args=(upload_queue,)).start()


class AzuraArchive(object):
    def __init__(
        self,
        play_file_path,
        play_file_name,
        image_file_path,
        show,
        name,
        playlist_name,
        station_id=None,
    ):
        self.play_file_path = play_file_path
        self.play_file_name = play_file_name
        self.play_file_size = None
        self.play_file_id = None
        self.image_file_path = image_file_path
        self.show = show
        self.name = name
        self.playlist_name = playlist_name
        self.playlist_id = None
        self.station_id = station_id or 1
        self.config = {
            "base": "{}/station/{}".format(
                app.config["AZURACAST_BASE_URL"], self.station_id
            ),
            "endpoint": {
                "files": "/files",
                "up_files": "/files/upload",
                "playlists": "/playlists",
                "playlist": "/playlist/",  # ID needed
                "file": "/file/",  # ID needed
                "batch_update": "/files/batch",
            },
            "headers": {"X-API-Key": app.config["AZURACAST_API_KEY"]},
            "chunk_byte": 1024 * 1024,  # 1M
        }

    def chunk_file_pieces(self,):
        total_chunk_num = math.ceil(self.play_file_size / self.config["chunk_byte"])
        return total_chunk_num

    def upload(self,):
        with open(self.play_file_path, "rb") as play_file:
            start = 0
            chunk_count = 1
            remaining_byte = self.play_file_size
            retry = 1
            tot_chunk_num = self.chunk_file_pieces()
            app.logger.debug("tot size {}".format(self.play_file_size))
            app.logger.debug("tot chunks {}".format(tot_chunk_num))
            while chunk_count <= tot_chunk_num:
                play_file.seek(start)
                chunk_byte = min(remaining_byte, self.config["chunk_byte"])
                # see: https://github.com/AzuraCast/AzuraCast/issues/2953
                payload = {
                    "file": "",
                    "flowChunkNumber": chunk_count,
                    "flowChunkSize": self.config["chunk_byte"],
                    "flowCurrentChunkSize": chunk_byte,
                    "flowFilename": self.play_file_name,
                    "flowIdentifier": "{}".format(
                        str(self.play_file_size) + self.play_file_name
                    ),
                    "flowTotalChunks": tot_chunk_num,
                    "flowTotalSize": self.play_file_size,
                }
                files = {"file_data": play_file.read(chunk_byte)}

                app.logger.debug(
                    "post chunk {}/{} w/ {}/{} bytes".format(
                        chunk_count, tot_chunk_num, chunk_byte, self.play_file_size,
                    )
                )
                try:
                    req = requests.post(
                        self.config["base"] + self.config["endpoint"]["up_files"],
                        data=payload,
                        files=files,
                        headers=self.config["headers"],
                    )
                    if req.ok:
                        chunk_count += 1
                        remaining_byte -= chunk_byte
                        start += chunk_byte
                        app.logger.debug("chunk posted! {} bytes remaining".format(remaining_byte))
                except requests.exceptions.RequestException as e:
                    # max 30 retries
                    if retry >= 30:
                        app.logger.debug("upload failed after 30 retries")
                        return False
                    app.logger.debug("Retry #{}: chunk post failed w/ {}!".format(retry, e,))
                    retry += 1
                    time.sleep(5)
                    continue
            return True
        return False

    def embedded_metadata(self,):
        # TODO use default image from show if no ep_image
        # not all files have metadate -- create if needed
        try:
            audio_meta = ID3(self.play_file_path)
            audio_meta.delete(delete_v1=True, delete_v2=True)
        except ID3NoHeaderError:
            audio_meta = ID3()
        image_format = self.image_file_path.split(".")[-1]  # TODO accept only png / jpg
        with open(self.image_file_path, "rb") as ima:
            audio_meta.add(
                # image
                APIC(
                    encoding=3,
                    data=ima.read(),
                    mime="image/{}".format(image_format),
                    description="{}".format(self.play_file_name),
                )
            )
            audio_meta.add(
                # episode host
                TPE1(encoding=3, text=self.show,)
            )
            audio_meta.add(
                # episode title
                TIT2(encoding=3, text=self.name,)
            )
            audio_meta.save(self.play_file_path, v2_version=3)
        # since we embed image to play_file we can only check the total play_file_size here
        self.play_file_size = os.path.getsize(self.play_file_path)
        return True

    def assign_playlist(self,):
        # PUT method; add episode to playlist
        if self.find_playlist_id():
            app.logger.info("Playlist id found successfully")
            app.logger.debug("Playlist id is {} \n playlist name is {}".format(self.playlist_id, self.playlist_name))
            if not self.empty_playlist():
                app.logger.info("Playlist is not empty")
                app.logger.info("Trying to wipe playlist")
                wiped = self.wipe_playlist_play_file()
                if not wiped:
                    app.logger.info("Couldn't wipe playlist")
                    return False
            app.logger.info("Playlist wiped")
            payload = {
                "do": "playlist",
                "files": [self.play_file_name],
                "playlists": [self.playlist_id],
            }
            app.logger.debug("Playlist payload \n {}".format(payload))
            r = requests.put(
                self.config["base"] + self.config["endpoint"]["batch_update"],
                headers=self.config["headers"],
                json=payload,
            )
            if r.ok:
                app.logger.info("Add to playlist request successful")
                return True
            app.logger.info("Add to playlist didn't succeed")
            app.logger.debug("Add to playlist request returned {}".format(r.status_code))
            app.logger.debug("Request response \n {}".format(r.content))
            return False
        return False

    def find_playlist_id(self,):
        # GET method; at arcsi side we only have the playlist_name
        # we need the corresponding id to query Azuracast API
        r = requests.get(
            self.config["base"] + self.config["endpoint"]["playlists"],
            headers=self.config["headers"],
        )
        if r.ok:
            for playlist in r.json():
                if playlist["name"] == self.playlist_name:
                    self.playlist_id = str(playlist["id"])
                    return True
            return False
        return False

    def empty_playlist(self):
        # we need to check that there are no other files in playlist
        req = requests.get(
            self.config["base"]
            + self.config["endpoint"]["playlist"]
            + self.playlist_id,
            headers=self.config["headers"],
        )
        if req.ok:
            playlist = req.json()
            if int(playlist["num_songs"]) == 0:
                return True
            return False
        return False

    def wipe_playlist_play_file(self,):
        # PUT method;
        # checks, selects & removes episodes assigned to playlist
        req = self.get_files()
        if req.ok:
            resp = req.json()
            payload_file_list = []
            for episode in resp:
                if episode["playlists"]:
                    playlist_match = [
                        True
                        for pl in episode["playlists"]
                        if pl["id"] == int(self.playlist_id)
                    ]
                    if playlist_match:
                        payload_file_list.append(episode["path"])
            payload = {"do": "delete", "files": payload_file_list}
            req = requests.put(
                self.config["base"] + self.config["endpoint"]["batch_update"],
                headers=self.config["headers"],
                json=payload,
            )
            if not req.ok:
                return False
            return True

    def get_files(self,):
        req = requests.get(
            self.config["base"] + self.config["endpoint"]["files"],
            headers=self.config["headers"],
        )
        return req


class BaseArchive(object):
    pass
