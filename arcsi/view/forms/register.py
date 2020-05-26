from wtforms import StringField
from flask_security.forms import RegisterForm


class ButtRegisterForm(RegisterForm):
    butt_user = StringField("Butt username", [])
    butt_pw = StringField("Butt password", [])
