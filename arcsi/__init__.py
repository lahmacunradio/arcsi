import os

from flask import Flask
from flask_migrate import Migrate

from arcsi.model.item import db

migrate = Migrate()

# TODO test config
def create_app():
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="ergya",
        SQLALCHEMY_DATABASE_URI="postgresql://localhost/<dbname>",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER="/example/path",
    )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    with app.app_context():
        db.init_app(app)
        db.create_all()
        migrate.init_app(app, db)

    from arcsi import api
    from arcsi import view

    app.register_blueprint(api.arcsi)
    app.register_blueprint(view.router)

    return app
