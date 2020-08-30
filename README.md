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
   * Mind this: https://github.com/mmmnmnm/lahmacun_arcsi/issues/5
2. app.env.template -> `app.env`
   * Set `FLASK_APP=run.py`
3. db.env.template -> `db.env`
4. srv.env.template -> `srv.env`
   * `Set DOMAIN=localhost`
5. nginx/http_arcsi.conf.template -> `nginx/arcsi.conf`

## Start docker
Run `docker-compose up -d`

## Run app
Hit http://localhost in your browser

