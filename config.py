import os

class Config:
    """Base configuration settings for the Flask application.

    Notes:
        - SECRET_KEY must be set via environment variable in production for security.
        - SQLALCHEMY_DATABASE_URI defaults to SQLite, but PostgreSQL is recommended
          for production due to full support for CheckConstraint and Enum types.
          Example for PostgreSQL: 'postgresql://user:password@localhost:5432/pos_db'
    """
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24).hex()
    if not SECRET_KEY and os.environ.get('FLASK_ENV') == 'production':
        raise ValueError("SECRET_KEY must be set in production environment")
    
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TOKEN_EXPIRATION_MINUTES = int(os.environ.get('TOKEN_EXPIRATION_MINUTES', 240))
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')  # Default for development only

class TestConfig(Config):
    """Configuration for testing."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory database for tests
    WTF_CSRF_ENABLED = False