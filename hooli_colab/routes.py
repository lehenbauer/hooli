""" hooli flask app route switches et al """

import os
from urllib.parse import urljoin
import uuid

from flask import (
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    flash,
    jsonify,
)
from flask_security import (
    login_required,
    current_user,
    logout_user,
    login_user,
    roles_accepted,
)

from flask_security.utils import hash_password, verify_password
from flask_wtf.csrf import CSRFProtect

from werkzeug.utils import secure_filename

from sqlalchemy import func
from itsdangerous import URLSafeTimedSerializer

from hooli_colab import app

from hooli_colab.models import User, MediaFile, Comments, MediaDirectory, Stars, Likes
from hooli_colab.forms import (
    CustomLoginForm,
    ForgotPasswordForm,
    ResetPasswordForm,
    EditMediaFileMetadataForm,
    AddCommentForm,
)
from hooli_colab.email import send_email
from hooli_colab.doodads import (rating_to_stars, log_message)

# from app import mail  # Ensure Flask-Mail is configured
# from werkzeug.security import generate_password_hash

csrf = CSRFProtect(app)


def get_or_create_directory(relative_dirpath):
    """Get or create a MediaDirectory object for the given directory path

    Args:
        relative_dirpath (str): The relative directory path.

    Returns:
        MediaDirectory: The MediaDirectory object for the given directory path.
    """
    from hooli_colab import db

    directory = MediaDirectory.query.filter_by(dirpath=relative_dirpath).first()
    if not directory:
        directory = MediaDirectory(dirpath=relative_dirpath)
        db.session.add(directory)
        db.session.commit()
    return directory


def user_likes(file_id):
    """
    Return True if the current user is logged in and has liked the media file, else False.

    Args:
        file_id (int): The ID of the media file to check if the user has liked.

    Returns:
        bool: True if the user has liked the media file, False otherwise.
    """
    if not current_user.is_authenticated:
        return False
    liked = Likes.query.filter_by(
        user_id=current_user.id, media_file_id=file_id
    ).first()
    if liked is None:
        liked = False
    return liked


def get_rating_summary(file_id):
    """
    Return a tuple containing the average rating and number of ratings for a media file.

    Args:
        file_id (int): The ID of the media file for which to retrieve the rating summary.

    Returns:
        tuple: A tuple containing the average rating (float) and the number of ratings (int).
    """
    from hooli_colab import db

    # Calculate average rating
    average_stars = (
        db.session.query(func.avg(Stars.stars))
        .filter(Stars.media_file_id == file_id)
        .scalar()
    )
    average_stars = round(average_stars, 2) if average_stars else 0.00

    # Count total number of ratings
    number_of_ratings = (
        db.session.query(func.count(Stars.id))
        .filter(Stars.media_file_id == file_id)
        .scalar()
    )

    return average_stars, number_of_ratings


def generate_reset_token(email):
    """Generate a password reset token for the given email address

    Args:
        email (str): The email address for which to generate the reset token.

    Returns:
        str: The generated password reset token.
    """

    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    return serializer.dumps(email, salt=app.config["SECURITY_PASSWORD_SALT"])


def verify_reset_token(token, expiration=3600):
    """Verify the password reset token

    Args:
        token (str): The password reset token to verify.
        expiration (int, optional): The expiration time in seconds. Defaults to 3600.

    Returns:
        str: The email address if the token is valid, None otherwise.
    """

    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    try:
        email = serializer.loads(
            token, salt=app.config["SECURITY_PASSWORD_SALT"], max_age=expiration
        )
    except:
        return None
    return email


# Modified send_reset_email function
def send_reset_email(user):
    """Send a password reset email to the user

    Args:
        user (User): The user object to whom the password reset email will be sent.
    """
    token = generate_reset_token(user.email)
    app_name = app.config["MYAPP_NAME"]
    reset_url = url_for("reset_password", token=token, _external=True)
    subject = f"Password Reset Request for {app_name}"
    body = f"Click the link to reset your {app_name} password: {reset_url}"
    send_email(to_email=user.email, subject=subject, content=body)


# Routes
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def browse_media(path):
    """Display all media files in the given directory path

    Args:
        path (str): The directory path to browse.
    """
    from hooli_colab import db

    full_path = os.path.join(app.config["MEDIA_ROOT"], path)
    if os.path.isdir(full_path):
        # Get or create directory metadata
        relative_dirpath = os.path.relpath(full_path, app.config["MEDIA_ROOT"])
        directory = get_or_create_directory(relative_dirpath)

        # Scan for media files
        media_files = []
        for entry in os.scandir(full_path):
            if entry.is_file() and entry.name.lower().endswith(
                (".mp3", ".wav", ".mp4", ".avi", ".pdf")
            ):
                relative_filepath = os.path.relpath(
                    entry.path, app.config["MEDIA_ROOT"]
                )
                media_file = MediaFile.query.filter_by(
                    filepath=relative_filepath
                ).first()
                if not media_file:
                    media_file = MediaFile(
                        filepath=relative_filepath,
                        filename=entry.name,
                        filetype=entry.name.split(".")[-1],
                        filesize=os.path.getsize(entry.path),
                        directory_id=directory.id,
                    )
                    db.session.add(media_file)
                    db.session.commit()
                media_files.append(media_file)

        media_files.sort(
            key=lambda x: (x.title.lower() if x.title else x.filename.lower())
        )
        media_files_with_ratings_and_likes = []
        for media_file in media_files:
            average_stars, number_of_ratings = get_rating_summary(media_file.id)
            liked = user_likes(media_file.id)
            media_files_with_ratings_and_likes.append(
                {
                    "media_file": media_file,
                    "average_stars": average_stars,
                    "number_of_ratings": number_of_ratings,
                    "liked": liked,
                    "unicode_stars": rating_to_stars(average_stars),
                }
            )
        return render_template(
            "browse.html",
            directory=directory,
            media_files=media_files_with_ratings_and_likes,
            path=path,
        )
    return "Not a directory", 404


@app.route("/directory/<int:dir_id>", methods=["GET", "POST"])
def edit_directory(dir_id):
    """
    Edit the metadata for a directory.

    This function handles both GET and POST requests to edit the metadata of a directory.
    On a GET request, it renders a form with the current metadata.
    On a POST request, it updates the directory metadata with the submitted form data.

    Args:
        dir_id (int): The ID of the directory to be edited.

    Returns:
        Response: The rendered template for GET requests.
        Response: A redirect to the browse_media page for POST requests.
    """
    from hooli_colab import db

    directory = MediaDirectory.query.get_or_404(dir_id)
    if request.method == "GET":
        return render_template(
            "edit_directory.html",
            directory=directory,
            title=directory.title,
            description=directory.description,
            image_path=directory.image_path,
        )
    if request.method == "POST":
        directory.title = request.form.get("title")
        directory.description = request.form.get("description")
        # Handle image upload if necessary
        if "image" in request.files:
            image = request.files["image"]
            if image and allowed_image(image.filename):
                filename = secure_filename(image.filename)
                unique_filename = str(uuid.uuid4()) + "_" + filename
                image.save(os.path.join(app.config["MEDIA_ROOT"], unique_filename))
                directory.image_path = unique_filename
        db.session.commit()
        flash("Directory information updated successfully.")
        return redirect(url_for("browse_media", path=directory.dirpath, _external=True))
    return render_template("edit_directory.html", directory=directory)


@app.route("/file/<int:file_id>", methods=["GET", "POST"])
def view_media(file_id):
    """
    Drill down into a single media file and display details such as rating and comments.

    This view handles both GET and POST requests. On GET requests, it fetches and displays
    the media file details, user comments, and ratings. On POST requests, it processes
    comment and rating submissions.

    Args:
        file_id (int): The ID of the media file to be viewed.

    Returns:
        Response: Renders the 'view_media.html' template with the media file details,
                  comments, user rating, average rating, number of ratings, and like status.
    """
    media_file = MediaFile.query.get_or_404(file_id)
    liked = user_likes(file_id)
    comment_form = AddCommentForm()

    # Fetch Comments
    comments = (
        Comments.query.filter_by(media_file_id=file_id)
        .order_by(Comments.timestamp.desc())
        .all()
    )

    # Get rating summary
    average_stars, number_of_ratings = get_rating_summary(file_id)

    # Fetch User Rating
    user_stars = None
    if current_user.is_authenticated:
        rating_record = Stars.query.filter_by(
            user_id=current_user.id, media_file_id=file_id
        ).first()
        if rating_record:
            user_stars = rating_record.stars

    return render_template(
        "view_media.html",
        media_file=media_file,
        comments=comments,
        user_rating=user_stars,
        average_rating=average_stars,
        number_of_ratings=number_of_ratings,
        liked=liked,
        comment_form=comment_form,
    )


@app.route("/download/<path:filename>")
def download_file(filename):
    """
    Download a file from the media directory.

    Args:
        filename (str): The name of the file to be downloaded.

    Returns:
        Response: A Flask response object that initiates the file download.
    """
    return send_from_directory(app.config["MEDIA_ROOT"], filename, as_attachment=True)


@app.route("/static/<path:filename>")
def static_files(filename):
    """
    Serve static files from the media directory.

    Args:
        filename (str): The name of the file to be served.

    Returns:
        Response: The response object containing the static file.
    """
    return send_from_directory("static", filename)


@app.route("/logout")
def logout():
    """
    Logs the user out and redirects them to the previous page or the media browsing page.

    This function logs out the current user by calling the `logout_user` function.
    After logging out, it redirects the user to the referring page if available,
    otherwise, it redirects to the 'browse_media' page.

    Returns:
        Response: A redirect response to the referring page or 'browse_media' page.
    """
    logout_user()
    return redirect(request.referrer or url_for("browse_media", _external=True))


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login.

    This function processes the login form submission. If the form is valid,
    it logs the user in and redirects them to the next page or the media browsing
    page. If the form is invalid, it flashes an error message and re-renders the
    login page with the form.

    Returns:
        Response: A redirect response to the next page or the media browsing page
                  if login is successful, or a rendered login page if login fails.
    """
    form = CustomLoginForm()
    if form.validate_on_submit():
        print(f'Login successful for "{form.user.email}" ({form.user.username})')
        login_user(form.user)

        # figure out where to direct to
        if not form.next.data:
            next_page = url_for("browse_media")
        else:
            next_link = form.next.data
            app_root = request.script_root  # e.g., "/hooli"
            if not app_root.endswith("/"):
                app_root += "/"
            relative_next = next_link.lstrip('/')
            next_page = urljoin(app_root, relative_next)

        print(f'next page {next_page}')
        return redirect(next_page)

    print(f'Login failed for "{form.username_or_email.data}"')
    if form.is_submitted():
        flash("Invalid credentials", "danger")
    form.next.data = request.args.get("next")
    return render_template("login.html", form=form)


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """
    Handle the forgot password process.

    This function renders the forgot password form and processes the form submission.
    If the form is valid and the email exists in the database, it sends a password reset email
    to the user and redirects to a page indicating that the email has been sent. If the email
    does not exist, it flashes an error message and redirects back to the forgot password page.

    Returns:
        Response: A redirect response to the appropriate page based on the form submission.
    """
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_reset_email(user)
            flash("A password reset email has been sent.", "info")
            # Pass email as query parameter
            return redirect(
                url_for(
                    "password_reset_email_sent", email=form.email.data, _external=True
                )
            )
        flash("Email address not found.", "danger")
        return redirect(url_for("forgot_password", _external=True))
    return render_template("forgot_password.html", form=form)


@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """
    Handle password reset requests.

    This route handles both GET and POST requests for resetting a user's password.
    It verifies the reset token, displays the reset password form, and updates the
    user's password if the form is submitted and validated.

    Args:
        token (str): The password reset token.

    Returns:
        Response: A Flask response object that renders the reset password template
        or redirects to another route based on the outcome of the request.
    """
    from hooli_colab import db

    email = verify_reset_token(token)
    if not email:
        flash("The reset link is invalid or has expired.", "danger")
        return redirect(url_for("forgot_password", _external=True))

    user = User.query.filter_by(email=email).first()
    form = ResetPasswordForm()

    if form.validate_on_submit():  # Changed to use validate_on_submit()
        user.password = hash_password(
            form.password.data
        )  # Use Flask-Security's hash_password
        db.session.commit()
        flash("Your password has been updated.", "success")
        return redirect(url_for("login", _external=True))

    return render_template("reset_password.html", form=form, token=token)


@app.route("/password-reset-email-sent")
def password_reset_email_sent():
    """
    Handles the password reset email sent page.

    This function retrieves the email address from the query parameters,
    masks it for privacy, and renders the password reset email sent page.
    If the email is not provided, it redirects the user to the login page.

    Returns:
        Response: A redirect to the login page if the email is not provided,
                  otherwise renders the password reset email sent page with
                  the masked email address.
    """
    email = request.args.get("email", "")  # Get email from query params
    if not email:
        return redirect(url_for("login", _external=True))
    # Mask email for privacy
    masked_email = email[:2] + "*" * (email.find("@") - 2) + email[email.find("@") :]
    return render_template("password_reset_email_sent.html", email=masked_email)


@app.route("/user-profile", methods=["GET"])
@login_required
def user_profile():
    """
    Renders the user profile page.

    Returns:
        Response: The rendered template for the user profile page.
    """
    return render_template("user_profile.html")


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """
    Handle the password change process for the current user.

    This function handles both GET and POST requests. For GET requests, it
    renders the password change form. For POST requests, it verifies the
    current password, checks if the new passwords match, updates the user's
    password, and commits the changes to the database.

    Returns:
        Response: A redirect to the appropriate URL or the rendered template
        for the password change form.
    """
    from hooli_colab import db

    if request.method == "POST":
        if not verify_password(request.form["current_password"], current_user.password):
            flash("Current password is incorrect", "danger")
            return redirect(url_for("change_password", _external=True))

        if request.form["new_password"] != request.form["confirm_password"]:
            flash("New passwords don't match", "danger")
            return redirect(url_for("change_password", _external=True))

        current_user.password = hash_password(request.form["new_password"])
        db.session.commit()
        flash("Password updated successfully", "success")
        return redirect(url_for("user_profile"))

    return render_template("change_password.html")


@app.route("/edit/<int:media_id>", methods=["GET", "POST"])
@roles_accepted("Admin", "Editor")
def edit_media_file_metadata(media_id):
    """
    Edit the metadata of a media file.

    This function retrieves a media file by its ID and allows the user to edit its metadata
    through a POST request. If the request method is POST, it updates the media file's
    attributes with the data from the
    request form, commits the changes to the database, flashes a success message, and
    redirects to the view media page. If the request method is not POST, it renders the
    edit media file metadata template.

    Args:
        media_id (int): The ID of the media file to be edited.

    Returns:
        Response: A redirect response to the view media page if the metadata is successfully
        updated, or a rendered template for editing the media file metadata.
    """
    from hooli_colab import db

    media_file = MediaFile.query.get_or_404(media_id)
    form = EditMediaFileMetadataForm(obj=media_file)

    if form.validate_on_submit():
        form.populate_obj(media_file)
        db.session.commit()
        flash("Media file metadata updated successfully.", "success")
        return redirect(url_for("view_media", file_id=media_id, _external=True))
    return render_template(
        "edit_media_file_metadata.html", media_file=media_file, form=form
    )


@app.route("/toggle_like/<int:file_id>", methods=["POST"])
def toggle_like(file_id):
    """
    Toggle the like status of a media file for the current user.

    This route handles the toggling of a like status for a media file identified by `file_id`.
    If the user is not authenticated, it returns a JSON response indicating the user
    is not authenticated.
    If the user has already liked the media file, the like is removed (unliked).
    If the user has not liked the media file, a new like is added.

    Args:
        file_id (int): The ID of the media file to toggle the like status for.

    Returns:
        Response: A JSON response with the status of the like action ('liked' or 'unliked').
        If the user is not authenticated, returns a JSON response with status 'not_authenticated'
        and HTTP status code 401.
    """
    from hooli_colab import db

    if not current_user.is_authenticated:
        # flash(
        #    "You must be logged in to like a song. Please login or register.", "danger"
        # )
        return jsonify({"status": "not_authenticated"}), 401

    like = Likes.query.filter_by(user_id=current_user.id, media_file_id=file_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
        status = "unliked"
    else:
        new_like = Likes(
            user_id=current_user.id,
            media_file_id=file_id,
            ip_address=request.remote_addr,
        )
        db.session.add(new_like)
        db.session.commit()
        status = "liked"
    return jsonify({"status": status})


@app.route("/<int:media_id>/add_comment", methods=["POST"])
@login_required
def add_comment(media_id):
    from hooli_colab import db

    comment_form = AddCommentForm()
    if comment_form.validate_on_submit():
        comment = Comments(
            user_id=current_user.id,
            media_file_id=media_id,
            content=comment_form.comment.data,
            ip_address=request.remote_addr,
        )
        db.session.add(comment)
        db.session.commit()
        flash("Your comment has been added.", "success")

    return redirect(
        url_for(
            "view_media", file_id=media_id, comment_form=comment_form, _external=True
        )
    )


@app.route("/<int:media_id>/add_rating", methods=["POST"])
@login_required
def add_rating(media_id):
    from hooli_colab import db

    rating = request.form.get("rating")
    if rating:
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except ValueError:
            flash("Invalid rating value.", "danger")
            return redirect(url_for("view_media", file_id=media_id, _external=True))

        existing_rating = Stars.query.filter_by(
            user_id=current_user.id, media_file_id=media_id
        ).first()
        if existing_rating:
            existing_rating.stars = rating
            flash("Your rating has been updated.", "success")
        else:
            new_rating = Stars(
                user_id=current_user.id,
                media_file_id=media_id,
                stars=rating,
                ip_address=request.remote_addr,
            )
            db.session.add(new_rating)
            flash("Your rating has been submitted.", "success")
        db.session.commit()
        return redirect(url_for("view_media", file_id=media_id, _external=True))
    flash("Rating is required.", "danger")
    return redirect(url_for("view_media", file_id=media_id, _external=True))


@app.route("/delete_comment/<int:comment_id>", methods=["POST"])
@roles_accepted("Admin", "Editor")
def delete_comment(comment_id):
    from hooli_colab import db

    # if not current_user.has_role("Admin") and not current_user.has_role("Editor"):
    #    flash("You do not have permission to delete comments.", "danger")
    #    return redirect(url_for("view_media", _external=True))

    comment = Comments.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash("Comment has been deleted.", "success")
    return redirect(
        url_for("view_media", file_id=comment.media_file_id, _external=True)
    )
