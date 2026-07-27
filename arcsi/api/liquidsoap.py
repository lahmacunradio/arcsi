import datetime
import jinja2
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

environment.filters['start_time'] = get_start_time
environment.filters['end_time'] = get_end_time
environment.filters['normalise'] = normalise

def get_playlist_init_template():
    f_str = """{% for show in shows%}
playlist_{{ show.playlist_name|normalise }} = playlist(id=\"playlist_{{ show.playlist_name|normalise }}\",mime_type=\"audio/x-mpegurl\",mode=\"randomize\",reload_mode=\"watch\",\"/var/azuracast/stations/lahmacun_radio/playlists/playlist_{{ show.playlist_name|normalise }}.m3u\")
playlist_{{ show.playlist_name|normalise }} = cue_cut(id=\"cue_playlist_{{ show.playlist_name|normalise }}\", playlist_{{ show.playlist_name|normalise }})
    {% endfor %}"""
    return f_str

def make_playlist_init_script(shows):
    tpl = environment.from_string(get_playlist_init_template())
    return tpl.render(shows = shows)

def get_playlist_schedule_template():
    f_str = """{% for show in shows %}
    ({ {{-show.day }}w and {{ show.start|start_time }}-{{ show.end|end_time-}} }, once(playlist_{{ show.playlist_name|normalise }})),
    {%-endfor %}"""
    return f_str

def make_playlist_schedule_script(shows):
    tpl = environment.from_string(get_playlist_schedule_template())
    return tpl.render(shows = shows)