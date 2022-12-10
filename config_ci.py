import os

# APP SECRET
SECRET_KEY = "yoursecretkeynotinversioncontrol"  # Never share! This is used to sign session. Note: https://github.com/pallets/itsdangerous/issues/41#issuecomment-69416785

# DB
# Set in db.env

SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@localhost:5432/{}".format(
    os.getenv("POSTGRES_USER"), os.getenv("POSTGRES_PASSWORD"), os.getenv("POSTGRES_DB")
)  # used by Sqlalchemy ORM; can be Mysql, Postgresql, sqlite, mongo etc.

SQLALCHEMY_TRACK_MODIFICATIONS = (
    False  # https://github.com/pallets/flask-sqlalchemy/issues/365
)

# AUTHENTICATION
# This enables Flask-Security to handle /register /login etc. so all-in-all: authentication
# https://pythonhosted.org/Flask-Security/configuration.html
SECURITY_SEND_REGISTER_EMAIL = True
SECURITY_REGISTERABLE = True
SECURITY_PASSWORD_SALT = "some_salt"
SECURITY_USE_VERIFY_PASSWORD_CACHE = True

# ARCSI CONF
UPLOAD_FOLDER = "uploads"  # this is where arcsi stores uploadable files temporarily
ALLOWED_EXTENSIONS = ["mp3", "gif", "jpg", "jpeg", "png"]

ARCHIVE_REGION = os.getenv("ARCHIVE_REGION")
ARCHIVE_HOST_BASE_URL = os.getenv("ARCHIVE_HOST_BASE_URL")
ARCHIVE_ENDPOINT = os.getenv("ARCHIVE_ENDPOINT")
ARCHIVE_API_KEY = os.getenv("ARCHIVE_API_KEY")
ARCHIVE_SECRET_KEY = os.getenv("ARCHIVE_SECRET_KEY")
AZURACAST_BASE_URL = os.getenv("AZURACAST_BASE_URL")
AZURACAST_API_KEY = os.getenv("AZURACAST_API_KEY")