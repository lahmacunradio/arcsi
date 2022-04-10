#!/bin/sh
python3 -m flask db upgrade
gunicorn --worker-tmp-dir /dev/shm -w 1 --worker-class=gthread --threads 4 -b 127.0.0.1:5666 --log-file /app/aguni.log --log-level info "arcsi:create_app('../config_ci.py')"
