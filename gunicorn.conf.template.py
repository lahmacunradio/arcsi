# https://gunicorn.org/reference/settings/
worker_tmp_dir = "/dev/shm"
timeout = 30
workers = 2
worker_class = "gthread"
threads = 2
bind = ["0.0.0.0:5666"]
errorlog = "/app/aguni.log"
