import datetime
import jinja2
from flask import current_app as app
from arcsi.api.utils import normalise


class Scheduler(object):

    def __init__(self):
        self.environment = jinja2.Environment()
        self.environment.filters["start_time"] = Scheduler.get_start_time
        self.environment.filters["end_time"] = Scheduler.get_end_time
        self.environment.filters["normalise"] = normalise

    def get_hour(timestamp):
        return datetime.datetime.strptime(timestamp, "%H:%M:%S").hour

    def get_minute(timestamp):
        return datetime.datetime.strptime(timestamp, "%H:%M:%S").minute

    def get_start_time(timestamp):
        hour = Scheduler.get_hour(timestamp)
        minute = Scheduler.get_minute(timestamp)
        return "{}h{}m".format(hour, minute)

    def get_end_time(timestamp):
        hour = Scheduler.get_hour(timestamp)
        minute = Scheduler.get_minute(timestamp)
        if minute == 0:
            hour = hour - 1
            minute = 58
        else:
            minute = minute - 2
        return "{}h{}m".format(hour, minute)


class LiquidsoapScheduler(Scheduler):

    def __init__(self):
        super().__init__()
        self.config = {"liquidsoap_version": app.config["LIQUIDSOAP_VERSION"]}

    def get_playlist_init_template(self):
        playlist_init_file = open(
            "/app/arcsi/templates/schedule/ls_playlist_init_{}.tpl".format(
                self.config["liquidsoap_version"]
            ),
            "r",
        )
        template = playlist_init_file.read()
        playlist_init_file.close()
        return template

    def make_playlist_init_script(self, shows):
        tpl = self.environment.from_string(self.get_playlist_init_template())
        return tpl.render(shows=shows)

    def get_playlist_schedule_template(self):
        playlist_schedule_file = open(
            "/app/arcsi/templates/schedule/ls_playlist_schedule_{}.tpl".format(
                self.config["liquidsoap_version"]
            ),
            "r",
        )
        template = playlist_schedule_file.read()
        playlist_schedule_file.close()
        return template

    def make_playlist_schedule_script(self, shows):
        tpl = self.environment.from_string(self.get_playlist_schedule_template())
        return tpl.render(shows=shows)

    def get_schedule_template(self):
        playlist_schedule_file = open(
            "/app/arcsi/templates/schedule/ls_schedule_{}.tpl".format(
                self.config["liquidsoap_version"]
            ),
            "r",
        )
        template = playlist_schedule_file.read()
        playlist_schedule_file.close()
        return template

    def make_schedule_script(self, shows):
        playlist_init = self.make_playlist_init_script(shows)
        playlist_schedule = self.make_playlist_schedule_script(shows)
        tpl = self.environment.from_string(self.get_schedule_template())
        return tpl.render(
            playlist_init=playlist_init, playlist_schedule=playlist_schedule
        )
