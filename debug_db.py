from app import create_app
from models import db, User

app = create_app()

with app.app_context():
    users = db.session.query(User).all()
    print(f"Total users: {len(users)}")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Role: {user.role}, Active: {user.is_active}")
        
    admin = db.session.query(User).filter_by(username='admin').first()
    if admin:
        print(f"Admin found. Password hash length: {len(admin.password_hash)}")
    else:
        print("Admin user NOT found!")
