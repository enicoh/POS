from flask import Flask, render_template, send_from_directory, request, redirect, url_for, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from models import db, User, Role
from routes import init_app
from pos_routes import init_pos_app
from werkzeug.security import generate_password_hash
import logging
import os
import jwt as pyjwt
from datetime import datetime, timedelta
from functools import wraps
from config import Config, TestConfig

def create_app(config_class=Config):
    """Factory function to create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    logging.info(f"Application created with config: {config_class.__name__}")

    # Enable CORS
    allowed_origins = os.environ.get('FRONTEND_URL', 'http://localhost:3000').split(',')
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}})

    # Initialize database
    db.init_app(app)
    migrate = Migrate(app, db)

    # Register routes
    init_app(app)
    init_pos_app(app)
    
    # Authentication decorator for protected routes
    def require_auth(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if we're already on the login page to prevent redirect loops
            if request.path == '/login.html':
                return f(*args, **kwargs)
            
            token = request.cookies.get('auth_token')
            if not token:
                # Clear any existing auth token from localStorage via JavaScript
                response = redirect(url_for('login_page'))
                response.set_cookie('auth_token', '', expires=0)
                return response
            
            try:
                payload = pyjwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
                # Check if token is expired
                if payload.get('exp') < datetime.utcnow().timestamp():
                    response = redirect(url_for('login_page'))
                    response.set_cookie('auth_token', '', expires=0)
                    return response
                return f(*args, **kwargs)
            except (pyjwt.ExpiredSignatureError, pyjwt.InvalidTokenError):
                response = redirect(url_for('login_page'))
                response.set_cookie('auth_token', '', expires=0)
                return response
        return decorated_function
    
    # Add static file routes
    @app.route('/')
    def index():
        # Always redirect to login page to prevent direct access
        return redirect(url_for('login_page'))
    
    @app.route('/login.html')
    def login_page():
        return render_template('login.html')
    
    @app.route('/admin_dashboard.html')
    @require_auth
    def admin_dashboard():
        return render_template('admin_dashboard.html')
    
    @app.route('/cashier_pos.html')
    @require_auth
    def cashier_pos():
        return render_template('cashier_pos.html')
    
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory('static', filename)
    
    @app.route('/<filename>')
    def serve_js_files(filename):
        if filename.endswith('.js'):
            return send_from_directory('static', filename)
        return "File not found", 404

    return app

def apply_migrations(app):
    """Apply database migrations automatically on startup."""
    with app.app_context():
        try:
            db.create_all()  # Ensure tables are created
            logging.info("Database tables created or verified.")
        except Exception as e:
            logging.error(f"Error initializing database: {e}")

def init_database(app):
    """Create a default admin user if none exists."""
    with app.app_context():
        try:
            admin_password = app.config['ADMIN_PASSWORD']
            if not admin_password:
                raise ValueError("ADMIN_PASSWORD must be set")
            admin_exists = db.session.get(User, 1)  # Assume admin has id=1 or check by role
            if not admin_exists:
                default_admin = User(
                    username='admin',
                    password_hash=generate_password_hash(admin_password),
                    role=Role.ADMIN
                )
                db.session.add(default_admin)
                db.session.commit()
                logging.info("Default admin user created: username=admin")
            else:
                logging.info("Admin user already exists")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Database initialization error: {e}")

def setup_logging():
    """Configure logging to file and console."""
    # Réinitialiser les gestionnaires existants pour éviter les interférences
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)

    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app.log')
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    except PermissionError as e:
        print(f"Erreur : Impossible d'écrire dans {log_file}. Vérifiez les permissions. {e}")
        file_handler = logging.NullHandler()
    except Exception as e:
        print(f"Erreur lors de la configuration du fichier de log : {e}")
        file_handler = logging.NullHandler()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            logging.StreamHandler()
        ]
    )
    # Test immédiat de la journalisation
    logging.getLogger(__name__).info("Journalisation configurée avec succès pour app.log")

# Create app
app = create_app()
setup_logging()
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    logger.info("Starting POS application...")

    if not app.config.get("TESTING", False):
        apply_migrations(app)
        init_database(app)

    # Default port
    port = int(os.environ.get('PORT', 8080))

    try:
        logger.info(f"Running on http://127.0.0.1:{port}")
        app.run(
            debug=os.environ.get('FLASK_ENV') != 'production',
            port=port,
            host='127.0.0.1',
            use_reloader=False  # Désactiver le reloader pour éviter la double exécution
        )
    except OSError as e:
        logger.error(f"[ERROR] Could not start server: {e}")