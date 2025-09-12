#!/usr/bin/env python3
"""
Script to populate the database with sample coffee shop data
Updated to reflect current database state
"""

from app import app
from models import db, User, Category, Product, ProductSize, ProductModifier, Role
from werkzeug.security import generate_password_hash

def populate_sample_data():
    with app.app_context():
        # Create categories
        categories_data = [
            {'name': 'Coffee', 'description': 'Hot and cold coffee beverages'},
            {'name': 'Tea', 'description': 'Various tea options'},
            {'name': 'Pastries', 'description': 'Fresh baked goods'},
            {'name': 'Sandwiches', 'description': 'Fresh sandwiches and wraps'},
            {'name': 'Smoothies', 'description': 'Fresh fruit smoothies'}
        ]
        
        # Create categories
        for cat_data in categories_data:
            existing_category = Category.query.filter_by(name=cat_data['name']).first()
            if not existing_category:
                category = Category(name=cat_data['name'], description=cat_data['description'])
                db.session.add(category)
        
        db.session.commit()
        
        # Current products from database (after deletions)
        products_data = [
            {
                'name': 'Cookies',
                'price': 140,
                'stock': 2,
                'category_name': 'Coffee',
                'description': '',
                'image_url': '/static/uploads/27a87853-541c-444e-9300-3bb3c797901c.png',
                'sizes': [
                    {'name': 'Single', 'price_modifier': 0},
                    {'name': 'Double', 'price_modifier': 20}
                ],
                'modifiers': []
            },
            {
                'name': 'Mocha',
                'price': 100,
                'stock': 24,
                'category_name': 'Coffee',
                'description': 'Espresso with chocolate and steamed milk',
                'image_url': 'https://images.unsplash.com/photo-1572442388796-11668a67e53d?w=300&h=300&fit=crop',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Medium', 'price_modifier': 20},
                    {'name': 'Large', 'price_modifier': 40}
                ],
                'modifiers': [
                    {'name': 'Extra Shot', 'price_modifier': 15},
                    {'name': 'Decaf', 'price_modifier': 0},
                    {'name': 'Oat Milk', 'price_modifier': 10},
                    {'name': 'Almond Milk', 'price_modifier': 10},
                    {'name': 'Extra Chocolate', 'price_modifier': 10}
                ]
            },
            {
                'name': 'Iced Coffee',
                'price': 70,
                'stock': 16,
                'category_name': 'Coffee',
                'description': 'Cold brewed coffee served over ice',
                'image_url': '/static/uploads/a4d95b69-464e-4e67-9aea-0535f7eb1d07.png',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Medium', 'price_modifier': 20},
                    {'name': 'Large', 'price_modifier': 40}
                ],
                'modifiers': [
                    {'name': 'Extra Shot', 'price_modifier': 15},
                    {'name': 'Decaf', 'price_modifier': 0},
                    {'name': 'Oat Milk', 'price_modifier': 10},
                    {'name': 'Almond Milk', 'price_modifier': 10},
                    {'name': 'Vanilla Syrup', 'price_modifier': 5}
                ]
            },
            {
                'name': 'Green Tea',
                'price': 40,
                'stock': 50,
                'category_name': 'Tea',
                'description': 'Premium green tea leaves',
                'image_url': 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=300&h=300&fit=crop',
                'sizes': [
                    {'name': 'Regular', 'price_modifier': 0}
                ],
                'modifiers': [
                    {'name': 'Honey', 'price_modifier': 10},
                    {'name': 'Lemon', 'price_modifier': 5}
                ]
            },
            {
                'name': 'Chai Latte',
                'price': 60,
                'stock': 35,
                'category_name': 'Tea',
                'description': 'Spiced tea with steamed milk',
                'image_url': 'https://images.unsplash.com/photo-1571934811356-5cc061b6821f?w=300&h=300&fit=crop',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Medium', 'price_modifier': 15},
                    {'name': 'Large', 'price_modifier': 30}
                ],
                'modifiers': [
                    {'name': 'Oat Milk', 'price_modifier': 10},
                    {'name': 'Almond Milk', 'price_modifier': 10},
                    {'name': 'Extra Spice', 'price_modifier': 5}
                ]
            },
            {
                'name': 'Muffin',
                'price': 50,
                'stock': 8,
                'category_name': 'Pastries',
                'description': 'Fresh baked muffin',
                'image_url': 'https://images.unsplash.com/photo-1486427944299-d1955d23e34d?w=300&h=300&fit=crop',
                'sizes': [],
                'modifiers': [
                    {'name': 'Blueberry', 'price_modifier': 0},
                    {'name': 'Chocolate Chip', 'price_modifier': 5},
                    {'name': 'Banana Nut', 'price_modifier': 5}
                ]
            },
            {
                'name': 'Pokemon',
                'price': 123,
                'stock': 200,
                'category_name': 'Pastries',
                'description': '',
                'image_url': '/static/uploads/207810aa-74cb-4ba8-b661-4761c0041357.png',
                'sizes': [],
                'modifiers': []
            }
        ]
        
        # Create products
        for product_data in products_data:
            existing_product = Product.query.filter_by(name=product_data['name']).first()
            if not existing_product:
                category = Category.query.filter_by(name=product_data['category_name']).first()
                if category:
                    product = Product(
                        name=product_data['name'],
                        price=product_data['price'],
                        stock=product_data['stock'],
                        category_id=category.id,
                        description=product_data['description'],
                        image_url=product_data['image_url'],
                        is_active=True
                    )
                    db.session.add(product)
                    db.session.flush()  # Get the product ID
                    
                    # Create sizes
                    for size_data in product_data['sizes']:
                        size = ProductSize(
                            product_id=product.id,
                            name=size_data['name'],
                            price_modifier=size_data['price_modifier']
                        )
                        db.session.add(size)
                    
                    # Create modifiers
                    for modifier_data in product_data['modifiers']:
                        modifier = ProductModifier(
                            product_id=product.id,
                            name=modifier_data['name'],
                            price_modifier=modifier_data['price_modifier']
                        )
                        db.session.add(modifier)
        
        # Create users
        users_data = [
            {'username': 'admin', 'password': 'admin123', 'role': Role.ADMIN},
            {'username': 'cashier', 'password': 'cashier123', 'role': Role.CASHIER}
        ]
        
        for user_data in users_data:
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if not existing_user:
                user = User(
                    username=user_data['username'],
                    password_hash=generate_password_hash(user_data['password']),
                    role=user_data['role']
                )
                db.session.add(user)
        
        db.session.commit()
        print("Sample data populated successfully!")

if __name__ == "__main__":
    populate_sample_data()
