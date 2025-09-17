import logging
import os

from flask import Flask
from flask_ckeditor import CKEditor
from flask_security import Security, SQLAlchemySessionUserDatastore
from flask_mail import Mail
from flask_migrate import Migrate
from flask_swagger_ui import get_swaggerui_blueprint
from sqlalchemy.exc import ProgrammingError

from arcsi.model import db, item, role, show, tag, user
from arcsi.view.forms.register import ButtRegisterForm

ckeditor = CKEditor()
migrate = Migrate()
mail = Mail()


def create_app(config_file):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # set logger and log-handler and log-level so that Gunicorn and Flask share
    guni_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = guni_logger.handlers
    app.logger.setLevel(guni_logger.level)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError as e:
        # already exists
        pass

    app.config.from_pyfile(config_file)

    user_store = SQLAlchemySessionUserDatastore(db.session, user.User, role.Role)
    # TODO w/ user_store can create_role() etc.
    # https://pythonhosted.org/Flask-Security/api.html#flask_security.datastore.SQLAlchemyUserDatastore
    security = Security(app, user_store, register_form=ButtRegisterForm)

    with app.app_context():
        db.init_app(app)
        migrate.init_app(app, db)
        ckeditor.init_app(app)
        app.mailing = mail.init_app(app)

        """
        The application factory runs when `flask db upgrade` is called
        in entrypoint. At this stage we don't have `roles` relations available.
        So we let `user_store` fail silently on first try. 
        This allows the `db upgrade` to set up all relations, which enables
        us to create these roles once gunicorn starts.
        """
        try:
            # create arcsi roles:
            # `admin` => access to whole service,
            # `host` => acces to their show,
            # `guest` => acces to their episode
            user_store.find_or_create_role(name="admin", description="Radio staff")
            user_store.find_or_create_role(name="host", description="Show host")
            user_store.find_or_create_role(name="guest", description="Episode guest")
            db.session.commit()
        except ProgrammingError as err:
            pass

    from arcsi import api
    from arcsi import view

    app.register_blueprint(api.arcsi)
    app.register_blueprint(view.router)

    ### swagger specific ###
    SWAGGER_URL = "/doc"
    API_URL = "/static/docs/swagger.json"
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL, API_URL, config={"app_name": "Arcsi"}
    )
    app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

    return app
