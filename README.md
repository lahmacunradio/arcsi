# lahmacun_arcsi
Lahmacun's archivator  

# Local setup

## Check environment
Make sure you have Docker. 

## Get source code
1. `git clone ` this repository
2. `cd lahmacun_arcsi`

## Create environment
Create following template files:
1. config.template.py -> `config.py`
   * Replace line 5 with `SQLALCHEMY_DATABASE_URI = "postgresql://postgres:p0stgr3s@db/arcsi"` (https://github.com/mmmnmnm/lahmacun_arcsi/issues/7)
2. app.env.template -> `app.env`
   * Set `FLASK_APP=run.py`
3. db.env.template -> `db.env`
4. srv.env.template -> `srv.env`
   * `Set DOMAIN=localhost`
5. nginx/http_arcsi.conf.template -> `nginx/arcsi.conf`

## Start docker
Run `docker-compose up -d`

Note: 
   * You may need to comment out following line in `docker-compose.yml`: `/etc/letsencrypt:/etc/letsencrypt`
   * `arcsi/__init__.py` may need special treatment: https://github.com/mmmnmnm/lahmacun_arcsi/issues/8
   * If an entry point fails to execute on Windows (the sh interpreter will tell you that the file doesn't exist, which is probably not true), check if there are Windows-style (CRLF) line endings and change them to Unix-style ones (LF). 
   * FOR DEVELOPERS: You may want to add the `--reload` option for Gunicorn on [line]( https://github.com/mmmnmnm/lahmacun_arcsi/blob/42c0cbf3056af1dfdf49ba02f184db62a633c4dc/entrypoint.sh#L3) for "on-the-fly" application of changes to Python files (you don't need to down and up docker for the changes to apply). Use it only during development!


## Run app
Hit http://localhost in your browser
