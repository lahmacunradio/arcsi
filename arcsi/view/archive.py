import requests

from flask import current_app as app
from flask import render_template, request, url_for, jsonify
from flask_security import login_required
from flask_login import current_user

from arcsi.model import guard
from arcsi.view import router


@router.route("/")
# Flask-Security
# @login_required
def archive():
    return render_template(
        "archive/list_archive.html"
    )

@router.route("/api_key")
def api_key():
    username = "endre"
    password = "YhhU8Z4W2dVbKNf"
    hashed_password = guard.hash_password(password)
    app.logger.error("password: " + password)
    app.logger.error("hashed_password: " + hashed_password)
    #return jsonify(hashed_password)
    user = guard.authenticate(username, password)
    
    ret = {"access_token": guard.encode_jwt_token(user)}
    return (jsonify(ret), 200)
