{% for show in shows %}
({ {{-show.day }}w and {{ show.start|start_time }}-{{ show.end|end_time-}} }, once(playlist_{{ show.playlist_name|normalise }})),
{%-endfor %}