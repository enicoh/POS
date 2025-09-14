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
            {'name': 'Milk & Dairy', 'description': 'Milk, cream, and dairy products'},
            {'name': 'Juices & Water', 'description': 'Fresh juices, water, and soft drinks'},
            {'name': 'Pastries', 'description': 'Fresh baked goods and desserts'},
            {'name': 'Sandwiches', 'description': 'Fresh sandwiches and wraps'},
            {'name': 'Smoothies', 'description': 'Fresh fruit smoothies and shakes'},
            {'name': 'Snacks', 'description': 'Light snacks and treats'}
        ]
        
        # Create categories
        for cat_data in categories_data:
            existing_category = Category.query.filter_by(name=cat_data['name']).first()
            if not existing_category:
                category = Category(name=cat_data['name'], description=cat_data['description'])
                db.session.add(category)
        
        db.session.commit()
        
        # Comprehensive coffee shop products
        products_data = [
            # COFFEE CATEGORY
            {
                'name': 'Espresso',
                'price': 80,
                'stock': 50,
                'category_name': 'Coffee',
                'description': 'Rich, full-bodied espresso shot',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Single', 'price_modifier': 0},
                    {'name': 'Double', 'price_modifier': 20}
                ],
                'modifiers': [
                    {'name': 'Decaf', 'price_modifier': 0},
                    {'name': 'Extra Shot', 'price_modifier': 15}
                ]
            },
            {
                'name': 'Americano',
                'price': 90,
                'stock': 45,
                'category_name': 'Coffee',
                'description': 'Espresso with hot water',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Medium', 'price_modifier': 15},
                    {'name': 'Large', 'price_modifier': 30}
                ],
                'modifiers': [
                    {'name': 'Decaf', 'price_modifier': 0},
                    {'name': 'Extra Shot', 'price_modifier': 15}
                ]
            },
            {
                'name': 'Cappuccino',
                'price': 120,
                'stock': 40,
                'category_name': 'Coffee',
                'description': 'Espresso with steamed milk and foam',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Medium', 'price_modifier': 20},
                    {'name': 'Large', 'price_modifier': 40}
                ],
                'modifiers': [
                    {'name': 'Decaf', 'price_modifier': 0},
                    {'name': 'Extra Shot', 'price_modifier': 15},
                    {'name': 'Oat Milk', 'price_modifier': 10},
                    {'name': 'Almond Milk', 'price_modifier': 10},
                    {'name': 'Extra Foam', 'price_modifier': 5}
                ]
            },
            {
                'name': 'Latte',
                'price': 130,
                'stock': 35,
                'category_name': 'Coffee',
                'description': 'Espresso with steamed milk',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Medium', 'price_modifier': 20},
                    {'name': 'Large', 'price_modifier': 40}
                ],
                'modifiers': [
                    {'name': 'Decaf', 'price_modifier': 0},
                    {'name': 'Extra Shot', 'price_modifier': 15},
                    {'name': 'Oat Milk', 'price_modifier': 10},
                    {'name': 'Almond Milk', 'price_modifier': 10},
                    {'name': 'Vanilla Syrup', 'price_modifier': 10},
                    {'name': 'Caramel Syrup', 'price_modifier': 10}
                ]
            },
            {
                'name': 'Mocha',
                'price': 150,
                'stock': 30,
                'category_name': 'Coffee',
                'description': 'Espresso with chocolate and steamed milk',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Medium', 'price_modifier': 20},
                    {'name': 'Large', 'price_modifier': 40}
                ],
                'modifiers': [
                    {'name': 'Decaf', 'price_modifier': 0},
                    {'name': 'Extra Shot', 'price_modifier': 15},
                    {'name': 'Oat Milk', 'price_modifier': 10},
                    {'name': 'Almond Milk', 'price_modifier': 10},
                    {'name': 'Extra Chocolate', 'price_modifier': 10},
                    {'name': 'Whipped Cream', 'price_modifier': 15}
                ]
            },
            {
                'name': 'Iced Coffee',
                'price': 100,
                'stock': 25,
                'category_name': 'Coffee',
                'description': 'Cold brewed coffee served over ice',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Medium', 'price_modifier': 20},
                    {'name': 'Large', 'price_modifier': 40}
                ],
                'modifiers': [
                    {'name': 'Decaf', 'price_modifier': 0},
                    {'name': 'Extra Shot', 'price_modifier': 15},
                    {'name': 'Oat Milk', 'price_modifier': 10},
                    {'name': 'Almond Milk', 'price_modifier': 10},
                    {'name': 'Vanilla Syrup', 'price_modifier': 10},
                    {'name': 'Caramel Syrup', 'price_modifier': 10}
                ]
            },
            
            # TEA CATEGORY
            {
                'name': 'Green Tea',
                'price': 60,
                'stock': 40,
                'category_name': 'Tea',
                'description': 'Premium green tea leaves',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Regular', 'price_modifier': 0}
                ],
                'modifiers': [
                    {'name': 'Honey', 'price_modifier': 10},
                    {'name': 'Lemon', 'price_modifier': 5},
                    {'name': 'Ginger', 'price_modifier': 5}
                ]
            },
            {
                'name': 'Black Tea',
                'price': 60,
                'stock': 35,
                'category_name': 'Tea',
                'description': 'Classic black tea',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Regular', 'price_modifier': 0}
                ],
                'modifiers': [
                    {'name': 'Honey', 'price_modifier': 10},
                    {'name': 'Lemon', 'price_modifier': 5},
                    {'name': 'Milk', 'price_modifier': 5}
                ]
            },
            {
                'name': 'Chai Latte',
                'price': 110,
                'stock': 30,
                'category_name': 'Tea',
                'description': 'Spiced tea with steamed milk',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Medium', 'price_modifier': 15},
                    {'name': 'Large', 'price_modifier': 30}
                ],
                'modifiers': [
                    {'name': 'Oat Milk', 'price_modifier': 10},
                    {'name': 'Almond Milk', 'price_modifier': 10},
                    {'name': 'Extra Spice', 'price_modifier': 5},
                    {'name': 'Honey', 'price_modifier': 10}
                ]
            },
            {
                'name': 'Herbal Tea',
                'price': 70,
                'stock': 25,
                'category_name': 'Tea',
                'description': 'Caffeine-free herbal blend',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Regular', 'price_modifier': 0}
                ],
                'modifiers': [
                    {'name': 'Honey', 'price_modifier': 10},
                    {'name': 'Lemon', 'price_modifier': 5}
                ]
            },
            
            # MILK & DAIRY CATEGORY
            {
                'name': 'Fresh Milk',
                'price': 40,
                'stock': 100,
                'category_name': 'Milk & Dairy',
                'description': 'Fresh whole milk',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small Glass', 'price_modifier': 0},
                    {'name': 'Large Glass', 'price_modifier': 20}
                ],
                'modifiers': []
            },
            {
                'name': 'Oat Milk',
                'price': 50,
                'stock': 80,
                'category_name': 'Milk & Dairy',
                'description': 'Plant-based oat milk',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small Glass', 'price_modifier': 0},
                    {'name': 'Large Glass', 'price_modifier': 20}
                ],
                'modifiers': []
            },
            {
                'name': 'Almond Milk',
                'price': 50,
                'stock': 70,
                'category_name': 'Milk & Dairy',
                'description': 'Plant-based almond milk',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small Glass', 'price_modifier': 0},
                    {'name': 'Large Glass', 'price_modifier': 20}
                ],
                'modifiers': []
            },
            
            # JUICES & WATER CATEGORY
            {
                'name': 'Orange Juice',
                'price': 80,
                'stock': 60,
                'category_name': 'Juices & Water',
                'description': 'Fresh squeezed orange juice',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Large', 'price_modifier': 30}
                ],
                'modifiers': []
            },
            {
                'name': 'Apple Juice',
                'price': 70,
                'stock': 50,
                'category_name': 'Juices & Water',
                'description': 'Fresh apple juice',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Large', 'price_modifier': 30}
                ],
                'modifiers': []
            },
            {
                'name': 'Bottled Water',
                'price': 30,
                'stock': 200,
                'category_name': 'Juices & Water',
                'description': 'Pure spring water',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': '500ml', 'price_modifier': 0},
                    {'name': '1L', 'price_modifier': 10}
                ],
                'modifiers': []
            },
            {
                'name': 'Sparkling Water',
                'price': 40,
                'stock': 100,
                'category_name': 'Juices & Water',
                'description': 'Refreshing sparkling water',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': '330ml', 'price_modifier': 0},
                    {'name': '500ml', 'price_modifier': 10}
                ],
                'modifiers': []
            },
            
            # PASTRIES CATEGORY
            {
                'name': 'Croissant',
                'price': 80,
                'stock': 20,
                'category_name': 'Pastries',
                'description': 'Fresh baked buttery croissant',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [],
                'modifiers': [
                    {'name': 'Plain', 'price_modifier': 0},
                    {'name': 'Chocolate', 'price_modifier': 15},
                    {'name': 'Almond', 'price_modifier': 20}
                ]
            },
            {
                'name': 'Muffin',
                'price': 90,
                'stock': 15,
                'category_name': 'Pastries',
                'description': 'Fresh baked muffin',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [],
                'modifiers': [
                    {'name': 'Blueberry', 'price_modifier': 0},
                    {'name': 'Chocolate Chip', 'price_modifier': 10},
                    {'name': 'Banana Nut', 'price_modifier': 10}
                ]
            },
            {
                'name': 'Danish Pastry',
                'price': 100,
                'stock': 12,
                'category_name': 'Pastries',
                'description': 'Flaky pastry with sweet filling',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [],
                'modifiers': [
                    {'name': 'Apple', 'price_modifier': 0},
                    {'name': 'Cherry', 'price_modifier': 5},
                    {'name': 'Cheese', 'price_modifier': 10}
                ]
            },
            {
                'name': 'Chocolate Cake',
                'price': 150,
                'stock': 8,
                'category_name': 'Pastries',
                'description': 'Rich chocolate cake slice',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [],
                'modifiers': []
            },
            
            # SANDWICHES CATEGORY
            {
                'name': 'Turkey Sandwich',
                'price': 180,
                'stock': 10,
                'category_name': 'Sandwiches',
                'description': 'Fresh turkey with lettuce and tomato',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [],
                'modifiers': [
                    {'name': 'White Bread', 'price_modifier': 0},
                    {'name': 'Whole Wheat', 'price_modifier': 5},
                    {'name': 'Extra Turkey', 'price_modifier': 20},
                    {'name': 'Add Cheese', 'price_modifier': 15}
                ]
            },
            {
                'name': 'Veggie Wrap',
                'price': 160,
                'stock': 8,
                'category_name': 'Sandwiches',
                'description': 'Fresh vegetables in a tortilla wrap',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [],
                'modifiers': [
                    {'name': 'Hummus', 'price_modifier': 10},
                    {'name': 'Avocado', 'price_modifier': 15},
                    {'name': 'Extra Veggies', 'price_modifier': 10}
                ]
            },
            
            # SMOOTHIES CATEGORY
            {
                'name': 'Berry Smoothie',
                'price': 120,
                'stock': 20,
                'category_name': 'Smoothies',
                'description': 'Mixed berries with yogurt',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Large', 'price_modifier': 30}
                ],
                'modifiers': [
                    {'name': 'Protein Powder', 'price_modifier': 20},
                    {'name': 'Extra Berries', 'price_modifier': 15}
                ]
            },
            {
                'name': 'Banana Smoothie',
                'price': 100,
                'stock': 25,
                'category_name': 'Smoothies',
                'description': 'Creamy banana smoothie',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [
                    {'name': 'Small', 'price_modifier': 0},
                    {'name': 'Large', 'price_modifier': 30}
                ],
                'modifiers': [
                    {'name': 'Honey', 'price_modifier': 10},
                    {'name': 'Chocolate', 'price_modifier': 15}
                ]
            },
            
            # SNACKS CATEGORY
            {
                'name': 'Cookies',
                'price': 60,
                'stock': 30,
                'category_name': 'Snacks',
                'description': 'Fresh baked cookies',
                'image_url': '/static/placeholder-coffee.svg',
                'sizes': [],
                'modifiers': [
                    {'name': 'Chocolate Chip', 'price_modifier': 0},
                    {'name': 'Oatmeal Raisin', 'price_modifier': 5},
                    {'name': 'Sugar Cookie', 'price_modifier': 5}
                ]
            },
            {
                'name': 'Granola Bar',
                'price': 40,
                'stock': 50,
                'category_name': 'Snacks',
                'description': 'Healthy granola bar',
                'image_url': '/static/placeholder-coffee.svg',
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
