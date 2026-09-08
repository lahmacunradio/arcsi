{% for show in shows%}
playlist_{{ show.playlist_name|normalise }} = playlist(id="playlist_{{ show.playlist_name|normalise }}",mime_type="audio/x-mpegurl",mode="randomize",reload_mode="watch","/var/azuracast/stations/lahmacun_radio/playlists/playlist_{{ show.playlist_name|normalise }}.m3u")
playlist_{{ show.playlist_name|normalise }} = cue_cut(id="cue_playlist_{{ show.playlist_name|normalise }}", playlist_{{ show.playlist_name|normalise }})
{% endfor %}