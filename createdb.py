# oneshot to create any missing database tables.
from hooli_colab import app, db
from hooli_colab.models import MediaFile

with app.app_context():
    # Recreate the table
    db.create_all()
