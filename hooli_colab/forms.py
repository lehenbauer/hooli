# FILE: hooli_colab/forms.py

from flask_wtf import FlaskForm
from flask_security.forms import RegisterForm, LoginForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField, TextAreaField
from wtforms.validators import (
    DataRequired,
    ValidationError,
    Email,
    Length,
    EqualTo,
    Optional,
)
from flask_security.utils import verify_password


class ExtendedRegisterForm(RegisterForm):
    """
    ExtendedRegisterForm is a subclass of Flask Security's
    RegisterForm that adds a username field
    to the registration form. This username field is required.

    Attributes:
        username (StringField): A required field for the username.

    Methods:
        validate_username(field):
            Validates that the username is not already taken by querying the user_datastore.
            Raises a ValidationError if the username is already taken.

        validate_email(field):
            Validates that the email is not already registered by querying the user_datastore.
            Raises a ValidationError if the email is already registered.
    """

    username = StringField("Username", [DataRequired()])

    def validate_username(self, field):
        """
        Validates the username field to ensure the username is not already taken.

        Args:
            field (wtforms.Field): The form field containing the username to validate.

        Raises:
            ValidationError: If the username is already taken.
        """
        from hooli_colab import user_datastore

        if user_datastore.find_user(username=field.data):
            raise ValidationError("Username is already taken.")

    def validate_email(self, field):
        """
        Validates that the provided email address is not already registered.

        Args:
            field (wtforms.Field): The form field containing the email address to validate.

        Raises:
            ValidationError: If the email address is already registered.
        """
        from hooli_colab import user_datastore

        if user_datastore.find_user(email=field.data):
            raise ValidationError("Email address is already registered.")


# NB theoretically we can get rid of the custom validator that allows
# people to login by username or email by setting
# app.config["SECURITY_USERNAME_ENABLE"] = True
# class CustomLoginForm(LoginForm):


class CustomLoginForm(FlaskForm):
    """
    CustomLoginForm is a subclass of FlaskForm that provides a custom login form allowing users to log in using either their username or email.

    Attributes:
        username_or_email (StringField): A field for the user to input their username or email.
        password (PasswordField): A field for the user to input their password.
        next (HiddenField): A hidden field to store the next URL to redirect to after login.
        submit (SubmitField): A submit button for the form.

    Methods:
        validate(**kwargs): Validates the login by checking if the user exists by email or username and verifies the password.
    """

    username_or_email = StringField("Username or Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    next = HiddenField()
    submit = SubmitField("Login")

    def validate(self, **kwargs):
        """validate the login by finding the user by email or username
        and verifying the password"""
        from hooli_colab import user_datastore

        if not super(CustomLoginForm, self).validate(**kwargs):
            return False

        user = user_datastore.find_user(
            email=self.username_or_email.data
        ) or user_datastore.find_user(username=self.username_or_email.data)
        if not user:
            self.username_or_email.errors.append("Unknown username or email")
            return False

        if not verify_password(self.password.data, user.password):
            self.password.errors.append("Invalid password")
            return False

        self.user = user
        return True


class ForgotPasswordForm(FlaskForm):
    """
    ForgotPasswordForm is a form for users to request a password reset.

    Attributes:
        email (StringField): A field for the user's email address, with validators to ensure the field is not empty and contains a valid email address.
        submit (SubmitField): A field for submitting the form to request a password reset.
    """

    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Reset Password")


class ResetPasswordForm(FlaskForm):
    """
    ResetPasswordForm is a FlaskForm for resetting a user's password.

    Fields:
        password (PasswordField): A field for the new password with validators to ensure it is provided and at least 8 characters long.
        confirm_password (PasswordField): A field to confirm the new password with validators to ensure it is provided and matches the password field.
        submit (SubmitField): A submit button for the form.

    Methods:
        validate_password(field): Custom validator to ensure the password contains at least one uppercase letter, one lowercase letter, and one number.

    Raises:
        ValidationError: If the password does not meet the complexity requirements.
    """

    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long"),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Reset Password")

    def validate_password(self, field):
        """
        Custom validator to ensure password complexity.

        Args:
            field (Field): The field containing the password to validate.

        Raises:
            ValidationError: If the password does not contain at least one uppercase letter.
            ValidationError: If the password does not contain at least one lowercase letter.
            ValidationError: If the password does not contain at least one number.
        """
        password = field.data
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one number")


class EditMediaFileMetadataForm(FlaskForm):
    title = StringField("Title", validators=[Optional()])
    artist = StringField("Artist", validators=[Optional()])
    album = StringField("Album", validators=[Optional()])
    genre = StringField("Genre", validators=[Optional()])
    tags = StringField("Tags", validators=[Optional()])
    description = TextAreaField("Description", validators=[Optional()])
    image_path = StringField("Image Path", validators=[Optional()])


class AddCommentForm(FlaskForm):
    comment = TextAreaField(
        "Comment", validators=[DataRequired()], render_kw={"rows": 4, "cols": 80}
    )
    submit = SubmitField("Add Comment")

class MediaDirectoryForm(FlaskForm):
    dirpath = StringField('Directory Path', validators=[DataRequired(), Length(max=500)])
    title = StringField('Title', validators=[Optional(), Length(max=255)])
    description = TextAreaField('Description', validators=[Optional()])
    image_path = StringField('Image Path', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save')