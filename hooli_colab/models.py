from hooli_colab import db
from flask_security import UserMixin, RoleMixin
import uuid


class MediaDirectory(db.Model):
    """
    Model for a directory containing media files.

    Attributes:
        id (int): Primary key.
        dirpath (str): Unique path to the directory.
        title (str): Title of the directory.
        description (str): Description of the directory.
        image_path (str): Path to the directory's image.
        media_files (List[MediaFile]): Related media files.
    """

    __tablename__ = "media_directory"
    id = db.Column(db.Integer, primary_key=True)
    dirpath = db.Column(db.String(500), unique=True, nullable=False)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    image_path = db.Column(db.String(500))
    media_files = db.relationship("MediaFile", backref="media_directory", lazy=True)


class MediaFile(db.Model):
    """
    Model for a media file.

    Attributes:
        id (int): Primary key for the media file.
        directory_id (int): Foreign key referencing the media directory.
        filepath (str): Path to the media file, must be unique.
        filename (str): Name of the media file.
        filetype (str): Type of the media file.
        filesize (int): Size of the media file in bytes.
        title (str, optional): Title of the media file.
        artist (str, optional): Artist of the media file.
        album (str, optional): Album of the media file.
        genre (str, optional): Genre of the media file.
        tags (str, optional): Tags associated with the media file.
        description (str, optional): Description of the media file.
        image_path (str, optional): Path to the image associated with the media file.
        comments (list): List of comments related to the media file.
        stars (list): List of star ratings related to the media file.
        likes (list): List of likes related to the media file.
    """

    __tablename__ = "media_file"
    id = db.Column(db.Integer, primary_key=True)
    directory_id = db.Column(
        db.Integer, db.ForeignKey("media_directory.id"), nullable=False
    )
    filepath = db.Column(db.String(500), unique=True, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filetype = db.Column(db.String(50), nullable=False)
    filesize = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255))
    artist = db.Column(db.String(255))
    album = db.Column(db.String(255))
    genre = db.Column(db.String(255))
    tags = db.Column(db.String(255))
    description = db.Column(db.Text)
    image_path = db.Column(db.String(500))
    comments = db.relationship("Comments", back_populates="media_file", lazy=True)
    stars = db.relationship("Stars", back_populates="media_file", lazy=True)
    likes = db.relationship("Likes", back_populates="media_file", lazy=True)


class Comments(db.Model):
    """
    Model for comments on media files.

    Attributes:
        id (int): Primary key for the comment.
        media_file_id (int): Foreign key referencing the media file.
        content (str): The content of the comment.
        ip_address (str): The IP address from which the comment was made.
        timestamp (datetime): The timestamp when the comment was created.
        user_id (int): Foreign key referencing the user who made the comment.
        user (User): Relationship to the User model.
        media_file (MediaFile): Relationship to the MediaFile model.
    """

    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    media_file_id = db.Column(
        db.Integer, db.ForeignKey("media_file.id"), nullable=False
    )
    content = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    timestamp = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    user = db.relationship("User", back_populates="comments", lazy=True)
    media_file = db.relationship("MediaFile", back_populates="comments", lazy=True)


class Stars(db.Model):
    """
    Model for stars i.e. ratings on media files.

    Attributes:
        id (int): Primary key for the stars table.
        media_file_id (int): Foreign key referencing the media file being rated.
        user_id (int): Foreign key referencing the user who gave the rating.
        stars (int): The rating given by the user.
        ip_address (str): The IP address from which the rating was given.
        timestamp (datetime): The time when the rating was given.

    Relationships:
        user (User): The user who gave the rating.
        media_file (MediaFile): The media file being rated.

    Constraints:
        __table_args__: Unique constraint on media_file_id and user_id to ensure a user can rate a media file only once.
    """

    __tablename__ = "stars"
    id = db.Column(db.Integer, primary_key=True)
    media_file_id = db.Column(
        db.Integer, db.ForeignKey("media_file.id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    stars = db.Column(db.Integer, nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    timestamp = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint("media_file_id", "user_id", name="_media_user_uc"),
    )

    user = db.relationship("User", back_populates="stars", lazy=True)
    media_file = db.relationship("MediaFile", back_populates="stars", lazy=True)


class Likes(db.Model):
    """
    Likes Model

    This model represents a 'like' on a media file by a user. It includes information
    about the media file being liked, the user who liked it, the like status (True = liked,
    False = not liked (or not there is not liked)), the IP
    address from which the like was made, and the timestamp of when the like was created.

    Attributes:
        id (int): Primary key for the likes table.
        media_file_id (int): Foreign key referencing the media file being liked.
        user_id (int): Foreign key referencing the user who liked the media file.
        like (bool): Boolean indicating whether the media file is liked.
        ip_address (str): IP address from which the like was made.
        timestamp (datetime): Timestamp of when the like was created.

    Relationships:
        user (User): Relationship to the User model, indicating the user who liked the media file.
        media_file (MediaFile): Relationship to the MediaFile model, indicating the media file that was liked.

    Constraints:
        __table_args__: Unique constraint ensuring a user can only like a specific media file once.
    """

    __tablename__ = "likes"
    id = db.Column(db.Integer, primary_key=True)
    media_file_id = db.Column(
        db.Integer, db.ForeignKey("media_file.id"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    like = db.Column(db.Boolean, nullable=False, default=False)
    ip_address = db.Column(db.String(45), nullable=False)
    timestamp = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint("media_file_id", "user_id", name="_media_user_uc"),
    )

    user = db.relationship("User", back_populates="likes", lazy=True)
    media_file = db.relationship("MediaFile", back_populates="likes", lazy=True)


roles_users = db.Table(
    "roles_users",
    db.Column("user_id", db.Integer(), db.ForeignKey("user.id")),
    db.Column("role_id", db.Integer(), db.ForeignKey("role.id")),
)


class Role(db.Model, RoleMixin):
    """
    Model for user roles in accordance with flask security.

    Attributes:
        id (int): The primary key for the role.
        name (str): The unique name of the role.
        description (str): A brief description of the role.
    """

    __tablename__ = "role"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    """
    Model for a user in accordance with flask security.

    Attributes:
        id (int): Primary key for the user.
        email (str): Unique email address of the user.
        password (str): Password for the user.
        active (bool): Indicates if the user is active.
        confirmed_at (datetime): Timestamp when the user was confirmed.
        fs_uniquifier (str): Unique identifier for Flask-Security.
        username (str): Unique username of the user.
        roles (list): List of roles associated with the user.
        comments (list): List of comments made by the user.
        stars (list): List of stars given by the user.
        likes (list): List of likes given by the user.
    """

    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    fs_uniquifier = db.Column(
        db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    username = db.Column(db.String(255), unique=True, nullable=False)
    roles = db.relationship(
        "Role", secondary=roles_users, backref=db.backref("users", lazy="dynamic")
    )
    comments = db.relationship("Comments", back_populates="user", lazy=True)
    stars = db.relationship("Stars", back_populates="user", lazy=True)
    likes = db.relationship("Likes", back_populates="user", lazy=True)
