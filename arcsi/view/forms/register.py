from wtforms import StringField
from flask_wtf.recaptcha import RecaptchaField
from flask_security.forms import RegisterFormV2


class ButtRegisterForm(RegisterFormV2):
    name = StringField("Username", [])
    recaptcha = RecaptchaField()
