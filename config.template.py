import os

# APP SECRET
SECRET_KEY = "yoursecretkeynotinversioncontrol"  # Never share! This is used to sign session. Note: https://github.com/pallets/itsdangerous/issues/41#issuecomment-69416785

# DB
# Set in db.env
SQLALCHEMY_DATABASE_URI = "postgresql://{}:{}@db/{}".format(
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
UPLOAD_FOLDER = "/abs/path/on/your/machine"  # this is where arcsi stores uploadable files temporarily
ALLOWED_EXTENSIONS = ["mp3", "gif", "jpg", "jpeg", "png"]
ARCHIVE_REGION = "jams4"  # used by boto3; depending on storage service might differ. AWS example: `eu-west-1`, DO example: `nyc1`
ARCHIVE_HOST_BASE_URL = (
    "https://ip-or-url-of-provid.er"  # used by boto3; an IP or public URL
)
ARCHIVE_ENDPOINT = "https://cdn.ed.ge"  # public URL or CDN edge
ARCHIVE_API_KEY = (
    "some-api-key-from-provider"  # used by boto3; access key from provider's interface
)
ARCHIVE_SECRET_KEY = "secret_hash"  # used by boto3; obtained from provider's interface

# AZURACAST CONF
AZURACAST_BASE_URL = "https://example-azura-stream.er/api"  # used by requests; base URL of your Azuracast station's API you wish to interact w/
AZURACAST_API_KEY = "secret_hash"  # used by requests; API key to authenticate w/ Azuracast station; obtained from Azuracast interface

if os.getenv("APP_ENV") == "development" or os.getenv("APP_ENV") == "production":
    HOST = "web"  # The service name for docker networking
    PREFERRED_URL_SCHEME = "https"
else:
    HOST = "localhost"
    PREFERRED_URL_SCHEME = "http"

PORT = 5666  # The application port nginx proxy is passing to
APP_BASE_URL = "http://{}:{}".format(HOST, PORT)

PAGE_SIZE = 12  # Configuration for paging results from a DB query

### EMAIL CONFIGURATION
# Used by Flask-Security for security, authorisation
MAIL_SERVER = "smtp.example.com"
MAIL_PORT = 000  # Update with actual number depending on TSL / SSL and your mail server provider
MAIL_USE_TLS = False
MAIL_USE_SSL = True
MAIL_USERNAME = "username"
MAIL_PASSWORD = "password"
