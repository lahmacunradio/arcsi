# lahmacun_arcsi
Lahmacun's archivator  

# Setup

## Check environment
Make sure you have `Python 3`, `psql` ready.

1. `python3 --version`
If not: https://www.python.org/downloads/
2. `psql --version`
If not: https://www.postgresql.org/download/

## Get source code
1. `git clone ` this repository
2. `cd lahmacun_arcsi`

## Create environment
Python uses the `venv` module to create app specific virtual environments. Here we will create 1. one, 2. enter, 3. install the libraries, dependencies into that environment.

1. `python3 -m venv venv` 
(You may name your environment as anything instead of `venv` as 2nd argument.)
2. `source ./venv/bin/activate`
(Exit w/ `deactivate`)
3. `pip install -r arcsi/requirements.txt`
4. `export FLASK_APP="run.py"`
5. `export FLASK_DEBUG=1`
We need to set the application we want Flask to serve and for development purposes (only) we also set debug to get couple of nice features from Flask & Werkzeug. More on Flask start: https://flask.palletsprojects.com/en/1.1.x/quickstart/

## Create app db
Flask has the great Flask-Migrate plugin that helps with versioning the db schema and makes it easy to set up new database connections. 

1. `createdb <db_name>`
Creates the database in postgres.
2. Set new db name in `arcsi/__init__.py` mapping
3. `flask db upgrade`
These commands create new db, connect app with it then we create the schema based on the latest version controlled migration version (see `migrations/versions` folder) 

### Add new schema change
If you change the models, do the following. This will change the db schema, so be careful. However, manual confirmation is always needed by Alembic so it's harder to break something by accident.

1. `flask db migrate -m "<optional_message>"`
This creates new migrations script which has to be reviewed before upgrade. New migration scripts should be committed to version control
2. `flask db upgrade`
Upgrade the current database schema according to changes.

## Run app
1. `flask run`
2. http://127.0.0.1:5000/

