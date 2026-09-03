#!/bin/sh
service cron start
uv run flask db upgrade
uv run gunicorn $GUNICORN_CMD_ARGS "arcsi:create_app('../config.py')"
