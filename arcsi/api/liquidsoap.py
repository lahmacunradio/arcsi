import datetime
import jinja2
from flask import current_app as app
from .utils import normalise

environment = jinja2.Environment()


def get_hour(timestamp):
    return datetime.datetime.strptime(timestamp, "%H:%M:%S").hour


def get_minute(timestamp):
    return datetime.datetime.strptime(timestamp, "%H:%M:%S").minute


def get_start_time(timestamp):
    hour = get_hour(timestamp)
    minute = get_minute(timestamp)
    return "{}h{}m".format(hour, minute)


def get_end_time(timestamp):
    hour = get_hour(timestamp)
    minute = get_minute(timestamp)
    if minute == 0:
        hour = hour - 1
        minute = 58
    else:
        minute = minute - 2
    return "{}h{}m".format(hour, minute)


environment.filters["start_time"] = get_start_time
environment.filters["end_time"] = get_end_time
environment.filters["normalise"] = normalise


def get_playlist_init_template():
    playlist_init_file = open(
        "/app/arcsi/templates/liquidsoap/playlist_init_{}.tpl".format(
            app.config["LIQUIDSOAP_VERSION"]
        ),
        "r",
    )
    template = playlist_init_file.read()
    playlist_init_file.close()
    return template


def make_playlist_init_script(shows):
    tpl = environment.from_string(get_playlist_init_template())
    return tpl.render(shows=shows)


def get_playlist_schedule_template():
    playlist_schedule_file = open(
        "/app/arcsi/templates/liquidsoap/playlist_schedule_{}.tpl".format(
            app.config["LIQUIDSOAP_VERSION"]
        ),
        "r",
    )
    template = playlist_schedule_file.read()
    playlist_schedule_file.close()
    return template


def make_playlist_schedule_script(shows):
    tpl = environment.from_string(get_playlist_schedule_template())
    return tpl.render(shows=shows)
