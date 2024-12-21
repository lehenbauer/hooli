"""
This module initializes the Flask application for Hooli Colab, including configuration settings,
database setup, and security features.

Modules and Packages:
- flask: Flask framework for web development.
- flask_mail: Flask extension for sending emails.
- flask_sqlalchemy: Flask extension for SQLAlchemy integration.
- flask_security: Flask extension for security features.
- hooli_colab.forms: Custom forms for login and registration.
- hooli_colab.email: Module for sending emails asynchronously.
- hooli_colab.models: Database models for the application.
- hooli_colab.routes: URL routes for the application.

Configuration:
- MEDIA_ROOT: Path to the media directory.
- APPLICATION_ROOT: URL prefix for the application.  We are rooted here even if we reference /,
    /login, /logout, etc.
- SQLALCHEMY_DATABASE_URI: URI for the SQLite database.
- SQLALCHEMY_TRACK_MODIFICATIONS: Flag to disable modification tracking.
- SECRET_KEY: Secret key for session management and flashing messages.
- SECURITY_REGISTERABLE: Flag to enable user registration.
- SECURITY_PASSWORD_SALT: Salt for password hashing.
- SECURITY_POST_LOGIN_VIEW: URL to redirect to after login.
- SECURITY_POST_LOGOUT_VIEW: URL to redirect to after logout.
- MAIL_SERVER: SMTP server for sending emails.
- MAIL_PORT: Port for the SMTP server.
- MAIL_USE_TLS: Flag to enable TLS for email.
- MAIL_USERNAME: Username for the SMTP server.
- MAIL_PASSWORD: Password for the SMTP server.
- MAIL_DEFAULT_SENDER: Default sender email address.
- SENDGRID_API_KEY: API key for SendGrid.
- SECURITY_EMAIL_SENDER: Email sender for security-related emails.
- SECURITY_EMAIL_SUBJECT_REGISTER: Subject for registration email.
- SECURITY_EMAIL_SUBJECT_PASSWORD_RESET: Subject for password reset email.
- SECURITY_SEND_REGISTER_EMAIL: Flag to send registration email.
- SECURITY_SEND_PASSWORD_CHANGE_EMAIL: Flag to send password change email.
- SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL: Flag to send password reset notice email.
- SECURITY_SEND_PASSWORD_RESET_EMAIL: Flag to send password reset email.
- SECURITY_SEND_PASSWORD_RESET_NOTICE_WITH_MESSAGE: Flag to send password reset notice with message.
- SECURITY_SEND_CONFIRMATION_EMAIL: Flag to send confirmation email.
- SECURITY_SEND_LOGIN_EMAIL: Flag to send login email.

Initialization:
- Flask app instance.
- Flask-Mail instance.
- SQLAlchemy instance.
- Flask-Security instance with custom forms and email task.
"""

import os
from dotenv import load_dotenv
from flask import Flask

from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore
from hooli_colab.forms import CustomLoginForm, ExtendedRegisterForm
from hooli_colab.email import send_mail_task

load_dotenv()

app = Flask(__name__)

mode = "dev"

# Configuration
MEDIA_ROOT = "/var/www/anodynename.com/public_html/hooli"
app.config["APPLICATION_ROOT"] = "/hooli"
#app.config["APPLICATION_ROOT"] = "/"

if mode == "dev":
    app.config["SESSION_COOKIE_PATH"] = "/"
else:
    app.config["SESSION_COOKIE_PATH"] = "/hooli"

app.config["MYAPP_NAME"] = "Hooli Colab"
app.config["MEDIA_ROOT"] = MEDIA_ROOT
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////var/www/hooli_colab/media.db"
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hooli.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = os.environ['APP_SECRET_KEY']  # Required for flashing messages

app.config["SECURITY_REGISTERABLE"] = True  # Required for registering users
app.config["SECURITY_PASSWORD_SALT"] = os.environ['SECURITY_PASSWORD_SALT']
app.config["SECURITY_POST_LOGIN_VIEW"] = "/login"
app.config["SECURITY_POST_LOGOUT_VIEW"] = "/logout"

sendgrid_key = os.environ['SENDGRID_KEY']
default_sender = os.environ['DEFAULT_SENDER']

app.config["MAIL_SERVER"] = "smtp.sendgrid.net"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "apikey"
app.config["MAIL_PASSWORD"] = sendgrid_key
app.config["MAIL_DEFAULT_SENDER"] = default_sender

app.config["SENDGRID_API_KEY"] = sendgrid_key

app.config["SECURITY_EMAIL_SENDER"] = default_sender
app.config["SECURITY_EMAIL_SUBJECT_REGISTER"] = "Welcome to Hooli Colab!"
app.config["SECURITY_EMAIL_SUBJECT_PASSWORD_RESET"] = "Password reset instructions"
app.config["SECURITY_SEND_REGISTER_EMAIL"] = True
app.config["SECURITY_SEND_PASSWORD_CHANGE_EMAIL"] = True
app.config["SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL"] = True
app.config["SECURITY_SEND_PASSWORD_RESET_EMAIL"] = True
app.config["SECURITY_SEND_PASSWORD_RESET_NOTICE_WITH_MESSAGE"] = True
app.config["SECURITY_SEND_CONFIRMATION_EMAIL"] = True
app.config["SECURITY_SEND_LOGIN_EMAIL"] = True

# Add CSRF configuration
app.config["WTF_CSRF_ENABLED"] = True

# secret key is taken from app.secret_key if not set here
#app.config["WTF_CSRF_SECRET_KEY"]='xxx'

app.config["SESSION_PROTECTION"] = "strong"
app.config["PERMANENT_SESSION_LIFETIME"] = 1800

mail = Mail(app)
db = SQLAlchemy(app)

# Import models and routes after initializing db
from hooli_colab import models, routes
from hooli_colab.models import User, Role


# Setup the user data store with SQLAlchemy, using the User and Role models
user_datastore = SQLAlchemyUserDatastore(db, User, Role)

# Initialize Flask-Security with the app, user data store, and custom forms and email task
security = Security(
    app,
    user_datastore,
    login_form=CustomLoginForm,
    register_form=ExtendedRegisterForm,
    send_mail_task=send_mail_task,
)
