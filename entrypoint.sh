#!/bin/sh
python3 -m flask db upgrade
gunicorn --worker-tmp-dir /dev/shm -t 30 -w 2 --worker-class=gthread --threads 2 -b 0.0.0.0:5666 --log-file /app/aguni.log --log-level info "arcsi:create_app('../config.py')"
