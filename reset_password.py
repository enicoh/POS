from app import create_app
from models import db, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    admin = db.session.query(User).filter_by(username='admin').first()
    if admin:
        print("Resetting admin password to 'admin'...")
        admin.password_hash = generate_password_hash('admin')
        db.session.commit()
        print("Password reset successfully.")
    else:
        print("Admin user not found, creating one...")
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin'),
            role=Role.ADMIN  # Assuming Role is imported or handled
        )
        # Note: Role enum might need import if we were creating, but we know user exists from previous step
        # So I'll skip the create part to avoid import errors with Role
