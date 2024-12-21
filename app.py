# driver program for the hooli flask app

import logging
import sys
from flask import Flask
from hooli_colab import app, db

# Configure logging
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
handler.setFormatter(formatter)

if not app.logger.handlers:
    app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5002, debug=True)
