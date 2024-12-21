import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import current_app


def send_email(to_email, subject, content):
    """Send an email using SendGrid API"""

    message = Mail(
        from_email=current_app.config["MAIL_DEFAULT_SENDER"],
        to_emails=to_email,
        subject=subject,
        html_content=content,
    )
    try:
        sg = SendGridAPIClient(current_app.config["SENDGRID_API_KEY"])
        response = sg.send(message)
        print(f"Status Code: {response.status_code}")
        print(f"Body: {response.body}")
        print(f"Headers: {response.headers}")
    except Exception as e:
        print(f"SendGrid Error: {str(e)}")


def send_mail_task(msg):
    """Send an email using the SendGrid API. This function is used by Flask-Security"""
    send_email(msg.recipients[0], msg.subject, msg.html)
