import requests

from flask import current_app as app
from flask_mail import email_dispatched, Message

# from arcsi import mail


def log_message(message):
    app.logger.debug(message.subject)


def write_test_message():
    msg = Message(
        subject="Arcsi test mail",
        recipients=["alavela05@gmail.com", "frenyo.endre@gmail.com"],
    )

    msg.html = "<p> Hello from Arcsi!</p>"
    email_dispatched.connect(log_message)
    return msg
    # mail.send(msg)

    #    email_dispatched.connect(log_message)


def send_test_message(msg):
    app.mailing.send(msg)

    email_dispatched.connect(log_message)
