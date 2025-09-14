#!/usr/bin/env python3
"""
Database setup script for Coffee Shop POS
This script initializes the database and creates default users.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import app, db
    from models import User, Role, Category, Product, ProductSize, ProductModifier
    from werkzeug.security import generate_password_hash
    
    print("Setting up database...")
    
    with app.app_context():
        try:
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("✓ Database tables created")
            
            # Ensure admin user exists
            print("Setting up admin user...")
            admin = User.query.filter_by(username='admin').first()
            if admin:
                admin.password_hash = generate_password_hash('admin')
                admin.is_active = True
                admin.role = Role.ADMIN
                print("✓ Admin user updated")
            else:
                admin = User(
                    username='admin', 
                    password_hash=generate_password_hash('admin'), 
                    role=Role.ADMIN, 
                    is_active=True
                )
                db.session.add(admin)
                print("✓ Admin user created")
            
            # Ensure cashier user exists
            print("Setting up cashier user...")
            cashier = User.query.filter_by(username='seller').first()
            if cashier:
                cashier.password_hash = generate_password_hash('seller')
                cashier.is_active = True
                cashier.role = Role.CASHIER
                print("✓ Cashier user updated")
            else:
                cashier = User(
                    username='seller', 
                    password_hash=generate_password_hash('seller'), 
                    role=Role.CASHIER, 
                    is_active=True
                )
                db.session.add(cashier)
                print("✓ Cashier user created")
            
            # Commit changes
            db.session.commit()
            print("✓ Database setup completed successfully")
            
        except Exception as e:
            print(f"❌ Database setup error: {e}")
            db.session.rollback()
            sys.exit(1)
            
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
