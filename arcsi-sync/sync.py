import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class SyncHandler(FileSystemEventHandler):
    def __init__(self):
        # eeeeeehhhhhhhh
        self.host = "http://127.0.0.1:5000/"
        self.add_api = "arcsi/item/add"

    def on_created(self, event):
        # get filename/path/etc
        # send api request
        # collect meta from azuradb through local network ip
        headers = {"Content-Type": "multipart/form-data"}
        payload = {
            "showname": "1. hullam",
            "showcover": "~~*>>*~~",
            "epnumber": 3,
            "eptitle": "beeeer",
            "epcover": "(9)",
            "epdate": "2020. 02. 20.",
        }
        req = requests.post(
            self.host + self.add_api, json=payload, data=event.src_path, headers=headers
        )
        if req.ok:
            print("warp-in complete")
        else:
            print(req.status_code)
            print(req.text)
            print(req.request.body)
            print(req.request.headers)
            print(req.request.url)


if __name__ == "__main__":
    path = "/example/path"
    handler = SyncHandler()
    obs = Observer()
    obs.schedule(handler, path)
    obs.start()
    # running it in a different tab for testing only -- tie this to run.py
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        obs.stop()
    obs.join()
