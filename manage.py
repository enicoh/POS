from flask.cli import FlaskGroup
from flask_migrate import Migrate
from app import app, db

"""
Command-line interface for managing the Flask application.

Usage:
    Initialize migrations:
        python manage.py db init
    Generate migration scripts:
        python manage.py db migrate
    Apply migrations:
        python manage.py db upgrade
"""

# Initialize Flask CLI and Migrate
migrate = Migrate(app, db)
cli = FlaskGroup(app)

if __name__ == "__main__":
    cli()