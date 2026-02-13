from flask import Blueprint, jsonify, request, Response, send_from_directory
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
import os
import uuid
import threading
import schedule
import time
from werkzeug.utils import secure_filename
from models import (
    db, User, Category, Product, ProductSize, ProductModifier, 
    Order, OrderItem, OrderItemModifier, Payment, Role, PaymentMethod, OrderType, CashRegisterSession, Settings
)
from werkzeug.security import generate_password_hash, check_password_hash
import jwt as pyjwt
import logging
import re
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from config import Config

pos_api = Blueprint('pos_api', __name__)
logger = logging.getLogger(__name__)

# File upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SECRET_KEY = Config.SECRET_KEY
TOKEN_EXPIRATION_MINUTES = Config.TOKEN_EXPIRATION_MINUTES

def _require_auth(required_role=None):
    """Decorator to require JWT authentication and optional role check."""
    def decorator(f):
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                logger.error("Missing or invalid Authorization header")
                return jsonify({'error': 'Authorization token required'}), 401
            try:
                token = auth_header.split(' ')[1]
                payload = pyjwt.decode(token, SECRET_KEY, algorithms=['HS256'])
                user = db.session.get(User, payload['user_id'])
                if not user or not user.is_active:
                    logger.error(f"Invalid or inactive user: user_id={payload['user_id']}")
                    return jsonify({'error': 'Invalid or inactive user'}), 401
                if required_role and user.role != required_role:
                    logger.error(f"Role {required_role.value} required, user has {user.role.value}")
                    return jsonify({'error': f'{required_role.value} role required'}), 403
                request.user = user
                return f(*args, **kwargs)
            except pyjwt.ExpiredSignatureError:
                logger.error("Token expired")
                return jsonify({'error': 'Token expired'}), 401
            except pyjwt.InvalidTokenError:
                logger.error("Invalid token")
                return jsonify({'error': 'Invalid token'}), 401
            except Exception as e:
                logger.error(f'Authentication error: {str(e)}')
                return jsonify({'error': 'Authentication failed'}), 401
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

# ---------- ADMIN DASHBOARD ENDPOINTS ----------

@pos_api.route('/admin/products', methods=['POST'])
@_require_auth(Role.ADMIN)
def create_product():
    """Create a new product with sizes and modifiers (admin only)."""
    logger.info("Processing create product request")
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'price', 'stock', 'category_id']):
        logger.error("Missing required fields in create product request")
        return jsonify({'error': 'Name, price, stock, and category_id required'}), 400

    if not isinstance(data['price'], int) or data['price'] <= 0:
        logger.error(f"Invalid price: {data['price']}")
        return jsonify({'error': 'Price must be a positive integer'}), 400

    if data['stock'] < 0:
        logger.error(f"Invalid stock value: {data['stock']}")
        return jsonify({'error': 'Stock cannot be negative'}), 400

    try:
        product = Product(
            name=data['name'],
            price=data['price'],
            stock=data['stock'],
            category_id=data['category_id'],
            description=data.get('description', ''),
            image_url=data.get('image_url', ''),
            low_stock_threshold=data.get('low_stock_threshold', 10)
        )
        db.session.add(product)
        db.session.flush()  # Get the product ID

        # Add sizes if provided
        if 'sizes' in data:
            for size_data in data['sizes']:
                size = ProductSize(
                    product_id=product.id,
                    name=size_data['name'],
                    price_modifier=size_data.get('price_modifier', 0)
                )
                db.session.add(size)

        # Add modifiers if provided
        if 'modifiers' in data:
            for modifier_data in data['modifiers']:
                modifier = ProductModifier(
                    product_id=product.id,
                    name=modifier_data['name'],
                    price_modifier=modifier_data.get('price_modifier', 0)
                )
                db.session.add(modifier)

        db.session.commit()
        logger.info(f"Product created: {product.name}")
        return jsonify(product.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        logger.error(f"Product name already exists: {data['name']}")
        return jsonify({'error': 'Product name already exists'}), 400

@pos_api.route('/admin/products/<int:product_id>', methods=['PUT'])
@_require_auth(Role.ADMIN)
def update_product(product_id):
    """Update a product (admin only)."""
    logger.info(f"Processing update product request for ID: {product_id}")
    product = db.session.get(Product, product_id)
    if not product:
        logger.error(f"Product not found: ID={product_id}")
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()
    if not data:
        logger.error("No data provided in update product request")
        return jsonify({'error': 'No data provided'}), 400

    try:
        if 'name' in data:
            product.name = data['name']
        if 'price' in data:
            if not isinstance(data['price'], int) or data['price'] <= 0:
                return jsonify({'error': 'Price must be a positive integer'}), 400
            product.price = data['price']
        if 'stock' in data:
            if data['stock'] < 0:
                return jsonify({'error': 'Stock cannot be negative'}), 400
            product.stock = data['stock']
        if 'category_id' in data:
            # Validate category exists
            new_category = db.session.get(Category, data['category_id'])
            if not new_category or not new_category.is_active:
                return jsonify({'error': 'Invalid category_id'}), 400
            product.category_id = data['category_id']
        if 'description' in data:
            product.description = data['description']
        if 'image_url' in data:
            product.image_url = data['image_url']
        if 'low_stock_threshold' in data:
            if data['low_stock_threshold'] < 0:
                return jsonify({'error': 'Low stock threshold cannot be negative'}), 400
            product.low_stock_threshold = data['low_stock_threshold']
        if 'is_active' in data:
            product.is_active = data['is_active']

        product.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Product updated: {product.name}")
        return jsonify(product.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        logger.error(f"Product name already exists: {data.get('name')}")
        return jsonify({'error': 'Product name already exists'}), 400

@pos_api.route('/admin/products/<int:product_id>/sizes', methods=['POST'])
@_require_auth(Role.ADMIN)
def add_product_size(product_id):
    """Add a size option to a product (admin only)."""
    logger.info(f"Processing add product size request for product ID: {product_id}")
    product = db.session.get(Product, product_id)
    if not product:
        logger.error(f"Product not found: ID={product_id}")
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()
    if not data or 'name' not in data:
        logger.error("Missing name in add product size request")
        return jsonify({'error': 'Name required'}), 400

    try:
        size = ProductSize(
            product_id=product_id,
            name=data['name'],
            price_modifier=data.get('price_modifier', 0)
        )
        db.session.add(size)
        db.session.commit()
        logger.info(f"Product size added: {size.name}")
        return jsonify(size.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        logger.error(f"Product size already exists: {data['name']}")
        return jsonify({'error': 'Product size already exists for this product'}), 400

@pos_api.route('/admin/products/<int:product_id>/modifiers', methods=['POST'])
@_require_auth(Role.ADMIN)
def add_product_modifier(product_id):
    """Add a modifier option to a product (admin only)."""
    logger.info(f"Processing add product modifier request for product ID: {product_id}")
    product = db.session.get(Product, product_id)
    if not product:
        logger.error(f"Product not found: ID={product_id}")
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()
    if not data or 'name' not in data:
        logger.error("Missing name in add product modifier request")
        return jsonify({'error': 'Name required'}), 400

    try:
        modifier = ProductModifier(
            product_id=product_id,
            name=data['name'],
            price_modifier=data.get('price_modifier', 0)
        )
        db.session.add(modifier)
        db.session.commit()
        logger.info(f"Product modifier added: {modifier.name}")
        return jsonify(modifier.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        logger.error(f"Product modifier already exists: {data['name']}")
        return jsonify({'error': 'Product modifier already exists for this product'}), 400

@pos_api.route('/admin/inventory', methods=['GET'])
@_require_auth(Role.ADMIN)
def get_inventory():
    """Get inventory status with low stock alerts (admin only)."""
    logger.info("Processing get inventory request")
    products = db.session.query(Product).filter_by(is_active=True).options(
        selectinload(Product.category),
        selectinload(Product.sizes),
        selectinload(Product.modifiers)
    ).all()

    inventory_data = []
    low_stock_products = []

    for product in products:
        product_data = product.to_dict()
        product_data['category_name'] = product.category.name
        product_data['sizes'] = [size.to_dict() for size in product.sizes if size.is_active]
        product_data['modifiers'] = [modifier.to_dict() for modifier in product.modifiers if modifier.is_active]
        
        if product.stock <= product.low_stock_threshold:
            product_data['low_stock_alert'] = True
            low_stock_products.append(product_data)
        else:
            product_data['low_stock_alert'] = False
        
        inventory_data.append(product_data)

    return jsonify({
        'inventory': inventory_data,
        'low_stock_products': low_stock_products,
        'total_products': len(inventory_data),
        'low_stock_count': len(low_stock_products)
    }), 200

@pos_api.route('/admin/inventory/<int:product_id>/stock', methods=['PUT'])
@_require_auth(Role.ADMIN)
def update_stock(product_id):
    """Update product stock (admin only)."""
    logger.info(f"Processing update stock request for product ID: {product_id}")
    product = db.session.get(Product, product_id)
    if not product:
        logger.error(f"Product not found: ID={product_id}")
        return jsonify({'error': 'Product not found'}), 404

    data = request.get_json()
    if not data or 'stock' not in data:
        logger.error("Missing stock in update stock request")
        return jsonify({'error': 'Stock required'}), 400

    if not isinstance(data['stock'], int) or data['stock'] < 0:
        logger.error(f"Invalid stock value: {data['stock']}")
        return jsonify({'error': 'Stock must be a non-negative integer'}), 400

    try:
        product.stock = data['stock']
        product.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Stock updated for product {product.name}: {product.stock}")
        return jsonify(product.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating stock: {str(e)}")
        return jsonify({'error': 'Failed to update stock'}), 400

@pos_api.route('/admin/products/<int:product_id>', methods=['DELETE'])
@_require_auth(Role.ADMIN)
def delete_product(product_id):
    """Delete a product (admin only)."""
    logger.info(f"Processing delete product request for ID: {product_id}")
    product = db.session.get(Product, product_id)
    if not product:
        logger.error(f"Product not found: ID={product_id}")
        return jsonify({'error': 'Product not found'}), 404

    try:
        # Try hard delete when possible
        from models import SaleItem, OrderItem
        referenced_in_sales = db.session.query(SaleItem).filter_by(product_id=product.id).first() is not None
        referenced_in_orders = db.session.query(OrderItem).filter_by(product_id=product.id).first() is not None

        if not referenced_in_sales and not referenced_in_orders:
            db.session.delete(product)
            db.session.commit()
            logger.info(f"Product hard-deleted: {product.name}")
            return jsonify({'message': 'Product deleted permanently'}), 200
        
        # If referenced, perform soft delete but free up unique name
        original_name = product.name
        product.is_active = False
        # Rename to free the unique constraint for future creations
        product.name = f"{original_name} [deleted #{product.id}]"
        product.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Product soft-deleted and renamed from {original_name} to {product.name}")
        return jsonify({'message': 'Product archived (historical references preserved)'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting product: {str(e)}")
        return jsonify({'error': 'Failed to delete product'}), 400

# ---------- CASHIER POS ENDPOINTS ----------

@pos_api.route('/pos/products', methods=['GET'])
@_require_auth()
def get_pos_products():
    """Get products for POS interface with sizes and modifiers."""
    logger.info("Processing get POS products request")
    products = db.session.query(Product).filter_by(is_active=True).options(
        selectinload(Product.category),
        selectinload(Product.sizes),
        selectinload(Product.modifiers)
    ).all()

    pos_products = []
    for product in products:
        if product.stock > 0:  # Only show products with stock
            product_data = product.to_dict()
            product_data['category_name'] = product.category.name
            product_data['sizes'] = [size.to_dict() for size in product.sizes if size.is_active]
            product_data['modifiers'] = [modifier.to_dict() for modifier in product.modifiers if modifier.is_active]
            pos_products.append(product_data)

    return jsonify(pos_products), 200

@pos_api.route('/pos/orders', methods=['POST'])
@_require_auth(Role.CASHIER)
def create_order():
    """Create a new order (cashier only)."""
    logger.info("Processing create order request")
    data = request.get_json()
    if not data or 'items' not in data:
        logger.error("Missing items in create order request")
        return jsonify({'error': 'Items required'}), 400

    session = db.session.query(CashRegisterSession).filter_by(
        user_id=request.user.id, status='open').first()
    if not session:
        logger.error("No open cash register session found")
        return jsonify({'error': 'No open cash register session'}), 400

    try:
        order = Order(
            user_id=request.user.id,
            session_id=session.id,
            customer_name=data.get('customer_name', ''),
            customer_phone=data.get('customer_phone', ''),
            order_type=OrderType[data.get('order_type', 'takeaway').upper()],
            notes=data.get('notes', '')
        )
        db.session.add(order)
        db.session.flush()  # Get the order ID

        subtotal = 0
        
        # Use a list to collect items, then add to order at the end to avoid partial flushes
        # causing issues with intermediate queries
        
        for item_data in data['items']:
            product = db.session.get(Product, item_data['product_id'])
            if not product:
                logger.error(f"Product not found: ID={item_data['product_id']}")
                return jsonify({'error': f'Product ID {item_data["product_id"]} not found'}), 404

            if item_data['quantity'] <= 0:
                logger.error(f"Invalid quantity: {item_data['quantity']}")
                return jsonify({'error': 'Quantity must be positive'}), 400

            if product.stock < item_data['quantity']:
                logger.error(f"Insufficient stock for product: {product.name}")
                return jsonify({'error': f'Insufficient stock for {product.name}'}), 400

            # Calculate unit price with size modifier
            unit_price = product.price
            size_id = None
            if 'size_id' in item_data and item_data['size_id']:
                size = db.session.get(ProductSize, item_data['size_id'])
                if size and size.is_active:
                    unit_price += size.price_modifier
                    size_id = size.id

            # Calculate total price for this item
            item_total = unit_price * item_data['quantity']
            
            # Temporary list for modifiers to calculate cost
            active_modifiers = []
            if 'modifier_ids' in item_data:
                for modifier_id in item_data['modifier_ids']:
                    modifier = db.session.get(ProductModifier, modifier_id)
                    if modifier and modifier.is_active:
                        active_modifiers.append(modifier)
                        item_total += modifier.price_modifier * item_data['quantity']

            order_item = OrderItem(
                product_id=product.id,
                size_id=size_id,
                quantity=item_data['quantity'],
                unit_price=unit_price,
                total_price=item_total,
                special_instructions=item_data.get('special_instructions', '')
            )
            
            # Add modifiers using relationship
            for modifier in active_modifiers:
                order_item_modifier = OrderItemModifier(
                    modifier_id=modifier.id,
                    price_modifier=modifier.price_modifier
                )
                order_item.modifiers.append(order_item_modifier)
            
            # Add item to order
            order.items.append(order_item)
            subtotal += item_total

        order.subtotal = subtotal
        order.tax_amount = 0  # No automatic tax - can be added manually if needed
        order.total = subtotal + order.tax_amount

        db.session.commit()
        logger.info(f"Order created: ID={order.id}, Total={order.total}")
        return jsonify(order.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating order: {str(e)}")
        return jsonify({'error': 'Failed to create order'}), 400

@pos_api.route('/pos/orders/<int:order_id>/complete', methods=['POST'])
@_require_auth(Role.CASHIER)
def complete_order(order_id):
    """Complete an order with payment (cashier only)."""
    logger.info(f"Processing complete order request for ID: {order_id}")
    order = db.session.get(Order, order_id)
    if not order:
        logger.error(f"Order not found: ID={order_id}")
        return jsonify({'error': 'Order not found'}), 404

    if order.user_id != request.user.id:
        logger.error(f"Unauthorized attempt to complete order: ID={order_id}")
        return jsonify({'error': 'Not authorized to complete this order'}), 403

    if order.status != 'pending':
        logger.error(f"Order already completed or cancelled: ID={order_id}")
        return jsonify({'error': 'Order already completed or cancelled'}), 400

    data = request.get_json()
    if not data or 'payment_method' not in data:
        logger.error("Missing payment_method in complete order request")
        return jsonify({'error': 'Payment method required'}), 400

    try:
        payment_method = PaymentMethod[data['payment_method'].upper()]
    except KeyError:
        logger.error(f"Invalid payment_method: {data['payment_method']}")
        return jsonify({'error': 'Invalid payment method'}), 400

    try:
        # Re-validate stock and decrement now
        for item in order.items:
            product = db.session.get(Product, item.product_id)
            if not product or not product.is_active:
                return jsonify({'error': f'Product no longer available: {item.product_id}'}), 400
            if product.stock < item.quantity:
                return jsonify({'error': f'Insufficient stock for {product.name}'}), 400
        for item in order.items:
            product = db.session.get(Product, item.product_id)
            product.stock -= item.quantity

        # Create payment
        payment = Payment(
            order_id=order.id,
            amount=order.total,
            payment_method=payment_method,
            transaction_id=data.get('transaction_id', ''),
            status='completed'
        )
        db.session.add(payment)

        # Update order status
        order.status = 'completed'
        order.completed_at = datetime.now(timezone.utc)
        order.payment = payment

        db.session.commit()
        logger.info(f"Order completed: ID={order.id}, Payment={order.total}")
        return jsonify({
            'order': order.to_dict(),
            'payment': payment.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error completing order: {str(e)}")
        return jsonify({'error': 'Failed to complete order'}), 400

@pos_api.route('/pos/orders', methods=['GET'])
@_require_auth()
def get_orders():
    """Get orders with optional filters."""
    logger.info("Processing get orders request")
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = db.session.query(Order)
    
    if request.user.role != Role.ADMIN:
        query = query.filter_by(user_id=request.user.id)
    
    if status:
        query = query.filter_by(status=status)
    
    try:
        if start_date:
            query = query.filter(Order.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Order.created_at <= datetime.fromisoformat(end_date))
    except ValueError:
        logger.error("Invalid date format in get orders request")
        return jsonify({'error': 'Invalid date format (use ISO format)'}), 400

    orders = query.options(
        selectinload(Order.items).selectinload(OrderItem.product),
        selectinload(Order.items).selectinload(OrderItem.size),
        selectinload(Order.items).selectinload(OrderItem.modifiers).selectinload(OrderItemModifier.modifier),
        selectinload(Order.payment)
    ).order_by(Order.created_at.desc()).all()

    return jsonify([{
        **order.to_dict(),
        'items': [{
            **item.to_dict(),
            'product_name': item.product.name,
            'size_name': item.size.name if item.size else None,
            'modifiers': [{
                'name': mod.modifier.name,
                'price_modifier': mod.price_modifier
            } for mod in item.modifiers]
        } for item in order.items],
        'payment': order.payment.to_dict() if order.payment else None
    } for order in orders]), 200

# ---------- CATEGORIES ENDPOINTS ----------

@pos_api.route('/categories', methods=['GET'])
@_require_auth()
def get_categories():
    """Retrieve all active categories."""
    logger.info("Processing get categories request")
    categories = db.session.query(Category).filter_by(is_active=True).all()
    return jsonify([category.to_dict() for category in categories]), 200

@pos_api.route('/categories', methods=['POST'])
@_require_auth(Role.ADMIN)
def create_category():
    """Create a new category (admin only)."""
    logger.info("Processing create category request")
    data = request.get_json()
    if not data or 'name' not in data:
        logger.error("Missing name in create category request")
        return jsonify({'error': 'Name required'}), 400

    try:
        category = Category(
            name=data['name'],
            description=data.get('description', '')
        )
        db.session.add(category)
        db.session.commit()
        logger.info(f"Category created: {category.name}")
        return jsonify(category.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        logger.error(f"Category name already exists: {data['name']}")
        return jsonify({'error': 'Category name already exists'}), 400

@pos_api.route('/categories/<int:category_id>', methods=['PUT'])
@_require_auth(Role.ADMIN)
def update_category(category_id):
    """Update a category (admin only)."""
    logger.info(f"Processing update category request for ID: {category_id}")
    category = db.session.get(Category, category_id)
    if not category:
        logger.error(f"Category not found: ID={category_id}")
        return jsonify({'error': 'Category not found'}), 404

    data = request.get_json()
    if not data or 'name' not in data:
        logger.error("Missing name in update category request")
        return jsonify({'error': 'Name required'}), 400

    try:
        category.name = data['name']
        category.description = data.get('description', category.description)
        category.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Category updated: {category.name}")
        return jsonify(category.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        logger.error(f"Category name already exists: {data['name']}")
        return jsonify({'error': 'Category name already exists'}), 400

@pos_api.route('/categories/<int:category_id>', methods=['DELETE'])
@_require_auth(Role.ADMIN)
def delete_category(category_id):
    """Delete a category (admin only)."""
    logger.info(f"Processing delete category request for ID: {category_id}")
    category = db.session.get(Category, category_id)
    if not category:
        logger.error(f"Category not found: ID={category_id}")
        return jsonify({'error': 'Category not found'}), 404

    try:
        # Soft delete - set is_active to False
        category.is_active = False
        category.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Category deleted: {category.name}")
        return jsonify({'message': 'Category deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting category: {str(e)}")
        return jsonify({'error': 'Failed to delete category'}), 400

# ---------- USERS ENDPOINTS ----------

@pos_api.route('/users', methods=['GET'])
@_require_auth(Role.ADMIN)
def get_users():
    """Retrieve all active users (admin only)."""
    logger.info("Processing get users request")
    users = db.session.query(User).filter_by(is_active=True).all()
    return jsonify([user.to_dict() for user in users]), 200

@pos_api.route('/users', methods=['POST'])
@_require_auth(Role.ADMIN)
def create_user():
    """Create a new user (admin only)."""
    logger.info("Processing create user request")
    data = request.get_json()
    if not data or not all(k in data for k in ['username', 'password', 'role']):
        logger.error("Missing required fields in create user request")
        return jsonify({'error': 'Username, password, and role required'}), 400

    if not re.match(r'^[a-zA-Z0-9_]{3,50}$', data['username']):
        logger.error(f"Invalid username format: {data['username']}")
        return jsonify({'error': 'Username must be 3-50 alphanumeric characters or underscores'}), 400

    try:
        role = Role[data['role'].upper()]
    except KeyError:
        logger.error(f"Invalid role: {data['role']}")
        return jsonify({'error': 'Invalid role'}), 400

    try:
        user = User(
            username=data['username'],
            password_hash=generate_password_hash(data['password']),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        logger.info(f"User created: {user.username}")
        return jsonify(user.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        logger.error(f"Username already exists: {data['username']}")
        return jsonify({'error': 'Username already exists'}), 400

@pos_api.route('/users/<int:user_id>', methods=['PUT'])
@_require_auth(Role.ADMIN)
def update_user(user_id):
    """Update a user (admin only)."""
    logger.info(f"Processing update user request for ID: {user_id}")
    user = db.session.get(User, user_id)
    if not user:
        logger.error(f"User not found: ID={user_id}")
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json()
    if not data:
        logger.error("No data provided in update user request")
        return jsonify({'error': 'No data provided'}), 400

    try:
        if 'username' in data:
            if not re.match(r'^[a-zA-Z0-9_]{3,50}$', data['username']):
                return jsonify({'error': 'Username must be 3-50 alphanumeric characters or underscores'}), 400
            user.username = data['username']
        if 'password' in data:
            user.password_hash = generate_password_hash(data['password'])
        if 'role' in data:
            try:
                role = Role[data['role'].upper()]
                user.role = role
            except KeyError:
                return jsonify({'error': 'Invalid role'}), 400
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"User updated: {user.username}")
        return jsonify(user.to_dict()), 200
    except IntegrityError:
        db.session.rollback()
        logger.error(f"Username already exists: {data.get('username')}")
        return jsonify({'error': 'Username already exists'}), 400

@pos_api.route('/users/<int:user_id>', methods=['DELETE'])
@_require_auth(Role.ADMIN)
def delete_user(user_id):
    """Delete a user (admin only)."""
    logger.info(f"Processing delete user request for ID: {user_id}")
    user = db.session.get(User, user_id)
    if not user:
        logger.error(f"User not found: ID={user_id}")
        return jsonify({'error': 'User not found'}), 404

    try:
        # Soft delete - set is_active to False
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"User deleted: {user.username}")
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting user: {str(e)}")
        return jsonify({'error': 'Failed to delete user'}), 400

@pos_api.route('/pos/orders/pending', methods=['GET'])
@_require_auth(Role.CASHIER)
def get_pending_orders():
    """Get all pending orders for the current user (cashier only)."""
    logger.info("Processing get pending orders request")
    orders = db.session.query(Order).filter_by(
        user_id=request.user.id,
        status='pending'
    ).order_by(Order.created_at.desc()).all()
    
    return jsonify([order.to_dict() for order in orders]), 200

@pos_api.route('/pos/orders/<int:order_id>', methods=['GET'])
@_require_auth(Role.CASHIER)
def get_order(order_id):
    """Get a specific order by ID (cashier only)."""
    logger.info(f"Processing get order request for ID: {order_id}")
    order = db.session.get(Order, order_id)
    if not order:
        logger.error(f"Order not found: ID={order_id}")
        return jsonify({'error': 'Order not found'}), 404

    if order.user_id != request.user.id:
        logger.error(f"Unauthorized attempt to access order: ID={order_id}")
        return jsonify({'error': 'Not authorized to access this order'}), 403

    return jsonify(order.to_dict()), 200

@pos_api.route('/pos/orders/<int:order_id>/cancel', methods=['POST'])
@_require_auth(Role.CASHIER)
def cancel_order(order_id):
    """Cancel a pending order (cashier only)."""
    logger.info(f"Processing cancel order request for ID: {order_id}")
    order = db.session.get(Order, order_id)
    if not order:
        logger.error(f"Order not found: ID={order_id}")
        return jsonify({'error': 'Order not found'}), 404

    if order.user_id != request.user.id:
        logger.error(f"Unauthorized attempt to cancel order: ID={order_id}")
        return jsonify({'error': 'Not authorized to cancel this order'}), 403

    if order.status != 'pending':
        logger.error(f"Order not in pending status: ID={order_id}")
        return jsonify({'error': 'Order is not pending'}), 400

    try:
        order.status = 'cancelled'
        order.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"Order cancelled: ID={order.id}")
        return jsonify({'message': 'Order cancelled successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error cancelling order: {str(e)}")
        return jsonify({'error': 'Failed to cancel order'}), 400

# ---------- ANALYTICS ENDPOINTS ----------

@pos_api.route('/analytics/sales', methods=['GET'])
@_require_auth(Role.ADMIN)
def get_sales_analytics():
    """Get sales analytics (admin only)."""
    logger.info("Processing get sales analytics request")
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Base query for completed orders without filtering out daily reset
    # We want ALL completed orders for the selected period
    query = db.session.query(Order).filter(
        Order.status == 'completed'
    )
    
    try:
        if start_date:
            query = query.filter(Order.completed_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Order.completed_at <= datetime.fromisoformat(end_date))
    except ValueError:
        logger.error("Invalid date format in get sales analytics request")
        return jsonify({'error': 'Invalid date format (use ISO format)'}), 400

    # Use eager loading to avoid N+1 queries
    orders = query.options(
        selectinload(Order.items).selectinload(OrderItem.product)
    ).all()
    
    total_sales = sum(order.total for order in orders)
    total_orders = len(orders)
    
    # Product sales analysis
    product_sales = {}
    for order in orders:
        for item in order.items:
            product_name = item.product.name
            if product_name not in product_sales:
                product_sales[product_name] = {'quantity': 0, 'revenue': 0}
            product_sales[product_name]['quantity'] += item.quantity
            product_sales[product_name]['revenue'] += item.total_price

    return jsonify({
        'total_sales': total_sales,
        'total_orders': total_orders,
        'product_sales': product_sales,
        'period': {
            'start_date': start_date,
            'end_date': end_date
        }
    }), 200

@pos_api.route('/analytics/sales/pdf', methods=['GET'])
@_require_auth(Role.ADMIN)
def generate_sales_report_pdf():
    """Generate sales report as PDF (admin only)."""
    logger.info("Processing generate sales report PDF request")
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = db.session.query(Order).filter_by(status='completed')
    
    try:
        if start_date:
            query = query.filter(Order.completed_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Order.completed_at <= datetime.fromisoformat(end_date))
    except ValueError:
        logger.error("Invalid date format in generate sales report PDF request")
        return jsonify({'error': 'Invalid date format (use ISO format)'}), 400

    # Use eager loading to avoid N+1 queries
    orders = query.options(
        selectinload(Order.items).selectinload(OrderItem.product)
    ).all()
    
    total_sales = sum(order.total for order in orders)
    total_orders = len(orders)
    
    # Product sales analysis
    product_sales = {}
    for order in orders:
        for item in order.items:
            product_name = item.product.name
            if product_name not in product_sales:
                product_sales[product_name] = {'quantity': 0, 'revenue': 0}
            product_sales[product_name]['quantity'] += item.quantity
            product_sales[product_name]['revenue'] += item.total_price

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Sales Report", styles['Title'])
    story.append(title)
    story.append(Paragraph("<br/>", styles['Normal']))
    
    # Period
    period_text = f"Period: {start_date or 'All time'} to {end_date or 'Present'}"
    story.append(Paragraph(period_text, styles['Normal']))
    story.append(Paragraph("<br/>", styles['Normal']))
    
    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Sales', f'DZD {total_sales:.2f}'],
        ['Total Orders', str(total_orders)]
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Paragraph("<br/>", styles['Normal']))
    
    # Product sales table
    if product_sales:
        story.append(Paragraph("Product Sales", styles['Heading2']))
        story.append(Paragraph("<br/>", styles['Normal']))

        product_data = [['Product', 'Quantity Sold', 'Price Per Unit (DZD)', 'Revenue (DZD)']]
        total_revenue = 0
        
        for product, data in sorted(product_sales.items(), key=lambda x: x[1]['revenue'], reverse=True):
            price_per_unit = data['revenue'] / data['quantity'] if data['quantity'] > 0 else 0
            product_data.append([
                product, 
                str(data['quantity']), 
                f"{price_per_unit:.2f}",
                f"{data['revenue']:.2f}"
            ])
            total_revenue += data['revenue']

        # Add total row
        product_data.append(['TOTAL', '', '', f"{total_revenue:.2f}"])

        product_table = Table(product_data)
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # Style the total row
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12)
        ]))

        story.append(product_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Return PDF
    filename = f'sales_report_{start_date or "all"}_{end_date or "present"}.pdf'
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@pos_api.route('/reports/sales/pdf', methods=['GET'])
@_require_auth(Role.ADMIN)
def generate_sales_report_pdf_alias():
    """Alias for PDF report to avoid client-side blockers on 'analytics' path."""
    logger.info("Processing generate sales report PDF (alias) request")
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = db.session.query(Order).filter_by(status='completed')
    
    try:
        if start_date:
            query = query.filter(Order.completed_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Order.completed_at <= datetime.fromisoformat(end_date))
    except ValueError:
        logger.error("Invalid date format in generate sales report PDF (alias) request")
        return jsonify({'error': 'Invalid date format (use ISO format)'}), 400
    
    # Use eager loading to avoid N+1 queries
    orders = query.options(
        selectinload(Order.items).selectinload(OrderItem.product)
    ).all()
    
    total_sales = sum(order.total for order in orders)
    total_orders = len(orders)
    
    # Product sales analysis
    product_sales = {}
    for order in orders:
        for item in order.items:
            product_name = item.product.name
            if product_name not in product_sales:
                product_sales[product_name] = {'quantity': 0, 'revenue': 0}
            product_sales[product_name]['quantity'] += item.quantity
            product_sales[product_name]['revenue'] += item.total_price
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Sales Report", styles['Title'])
    story.append(title)
    story.append(Paragraph("<br/>", styles['Normal']))
    
    # Period
    period_text = f"Period: {start_date or 'All time'} to {end_date or 'Present'}"
    story.append(Paragraph(period_text, styles['Normal']))
    story.append(Paragraph("<br/>", styles['Normal']))
    
    # Summary table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Sales', f'DZD {total_sales:.2f}'],
        ['Total Orders', str(total_orders)]
    ]
    
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(summary_table)
    story.append(Paragraph("<br/>", styles['Normal']))
    
    # Product sales table
    if product_sales:
        story.append(Paragraph("Product Sales", styles['Heading2']))
        story.append(Paragraph("<br/>", styles['Normal']))
        
        product_data = [['Product', 'Quantity Sold', 'Price Per Unit (DZD)', 'Revenue (DZD)']]
        total_revenue = 0
        
        for product, data in sorted(product_sales.items(), key=lambda x: x[1]['revenue'], reverse=True):
            price_per_unit = data['revenue'] / data['quantity'] if data['quantity'] > 0 else 0
            product_data.append([
                product,
                str(data['quantity']),
                f"{price_per_unit:.2f}",
                f"{data['revenue']:.2f}"
            ])
            total_revenue += data['revenue']
        
        # Add total row
        product_data.append(['TOTAL', '', '', f"{total_revenue:.2f}"])
        
        product_table = Table(product_data)
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12)
        ]))
        
        story.append(product_table)
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Return PDF
    filename = f'sales_report_{start_date or "all"}_{end_date or "present"}.pdf'
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )

@pos_api.route('/reports/sales/pdf/download', methods=['GET'])
def generate_sales_report_pdf_download():
    """PDF download endpoint that accepts JWT via query param 'token' for convenience.
    This avoids fetch() and lets browsers download directly even if extensions block XHR.
    """
    token = request.args.get('token')
    if not token and 'Authorization' in request.headers:
        # Fallback to header if present
        try:
            token = request.headers.get('Authorization', '').split(' ')[1]
        except Exception:
            token = None

    if not token:
        return jsonify({'error': 'Authorization token required'}), 401

    try:
        payload = pyjwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user = db.session.get(User, payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'error': 'Invalid or inactive user'}), 401
        # Only admins can download
        if user.role != Role.ADMIN:
            return jsonify({'error': 'admin role required'}), 403
    except pyjwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except pyjwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception:
        return jsonify({'error': 'Authentication failed'}), 401

    # Reuse the alias logic for generating PDF
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = db.session.query(Order).filter_by(status='completed')
    try:
        if start_date:
            query = query.filter(Order.completed_at >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Order.completed_at <= datetime.fromisoformat(end_date))
    except ValueError:
        return jsonify({'error': 'Invalid date format (use ISO format)'}), 400

    # Use eager loading to avoid N+1 queries
    orders = query.options(
        selectinload(Order.items).selectinload(OrderItem.product)
    ).all()

    total_sales = sum(order.total for order in orders)
    total_orders = len(orders)

    product_sales = {}
    for order in orders:
        for item in order.items:
            product_name = item.product.name
            if product_name not in product_sales:
                product_sales[product_name] = {'quantity': 0, 'revenue': 0}
            product_sales[product_name]['quantity'] += item.quantity
            product_sales[product_name]['revenue'] += item.total_price

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph("Sales Report", styles['Title'])
    story.append(title)
    story.append(Paragraph("<br/>", styles['Normal']))

    period_text = f"Period: {start_date or 'All time'} to {end_date or 'Present'}"
    story.append(Paragraph(period_text, styles['Normal']))
    story.append(Paragraph("<br/>", styles['Normal']))

    summary_data = [
        ['Metric', 'Value'],
        ['Total Sales', f'DZD {total_sales:.2f}'],
        ['Total Orders', str(total_orders)]
    ]
    summary_table = Table(summary_data)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    story.append(Paragraph("<br/>", styles['Normal']))

    if product_sales:
        story.append(Paragraph("Product Sales", styles['Heading2']))
        story.append(Paragraph("<br/>", styles['Normal']))
        product_data = [['Product', 'Quantity Sold', 'Price Per Unit (DZD)', 'Revenue (DZD)']]
        total_revenue = 0
        for product, data in sorted(product_sales.items(), key=lambda x: x[1]['revenue'], reverse=True):
            price_per_unit = data['revenue'] / data['quantity'] if data['quantity'] > 0 else 0
            product_data.append([product, str(data['quantity']), f"{price_per_unit:.2f}", f"{data['revenue']:.2f}"])
            total_revenue += data['revenue']
        product_data.append(['TOTAL', '', '', f"{total_revenue:.2f}"])
        product_table = Table(product_data)
        product_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 12)
        ]))
        story.append(product_table)

    doc.build(story)
    buffer.seek(0)
    filename = f"sales_report_{start_date or 'all'}_{end_date or 'present'}.pdf"
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )

# ---------- FILE UPLOAD ----------
@pos_api.route('/upload/image', methods=['POST'])
@_require_auth(Role.ADMIN)
def upload_image():
    """Upload an image file (admin only)."""
    logger.info("Processing image upload request")
    
    if 'file' not in request.files:
        logger.error("No file part in upload request")
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("No file selected for upload")
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        logger.error(f"File type not allowed: {file.filename}")
        return jsonify({'error': 'File type not allowed. Use PNG, JPG, JPEG, GIF, or WEBP'}), 400
    
    try:
        # Generate unique filename
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        filename = secure_filename(unique_filename)
        
        # Save file
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Return the URL for the uploaded file
        image_url = f'/static/uploads/{filename}'
        logger.info(f"Image uploaded successfully: {image_url}")
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image_url': image_url
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading image: {str(e)}")
        return jsonify({'error': 'Failed to upload image'}), 500

@pos_api.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files."""
    return send_from_directory(UPLOAD_FOLDER, filename)

# ---------- PRODUCT SIZES MANAGEMENT ----------

@pos_api.route('/admin/products/<int:product_id>/sizes', methods=['GET'])
@_require_auth(Role.ADMIN)
def get_product_sizes(product_id):
    """Get all sizes for a product (admin only)."""
    logger.info(f"Processing get product sizes request for product ID: {product_id}")
    try:
        product = Product.query.get_or_404(product_id)
        sizes = ProductSize.query.filter_by(product_id=product_id).all()
        
        return jsonify({
            'sizes': [size.to_dict() for size in sizes]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting product sizes: {str(e)}")
        return jsonify({'error': 'Failed to get product sizes'}), 500

@pos_api.route('/admin/products/<int:product_id>/sizes', methods=['POST'])
@_require_auth(Role.ADMIN)
def create_product_size(product_id):
    """Create a new size for a product (admin only)."""
    logger.info(f"Processing create product size request for product ID: {product_id}")
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'price_modifier' not in data:
            return jsonify({'error': 'Name and price_modifier are required'}), 400
        
        # Check if product exists
        product = Product.query.get_or_404(product_id)
        
        # Check if size name already exists for this product
        existing_size = ProductSize.query.filter_by(
            product_id=product_id, 
            name=data['name']
        ).first()
        
        if existing_size:
            return jsonify({'error': 'Size with this name already exists for this product'}), 400
        
        size = ProductSize(
            product_id=product_id,
            name=data['name'],
            price_modifier=data['price_modifier']
        )
        
        db.session.add(size)
        db.session.commit()
        
        logger.info(f"Product size created: {size.name} for product {product.name}")
        return jsonify(size.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating product size: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create product size'}), 500

@pos_api.route('/admin/sizes/<int:size_id>', methods=['PUT'])
@_require_auth(Role.ADMIN)
def update_product_size(size_id):
    """Update a product size (admin only)."""
    logger.info(f"Processing update product size request for size ID: {size_id}")
    try:
        size = ProductSize.query.get_or_404(size_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'name' in data:
            # Check if another size with this name exists for the same product
            existing_size = ProductSize.query.filter(
                ProductSize.product_id == size.product_id,
                ProductSize.name == data['name'],
                ProductSize.id != size_id
            ).first()
            
            if existing_size:
                return jsonify({'error': 'Size with this name already exists for this product'}), 400
            
            size.name = data['name']
        
        if 'price_modifier' in data:
            size.price_modifier = data['price_modifier']
        
        db.session.commit()
        
        logger.info(f"Product size updated: {size.name}")
        return jsonify(size.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error updating product size: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update product size'}), 500

@pos_api.route('/admin/sizes/<int:size_id>', methods=['DELETE'])
@_require_auth(Role.ADMIN)
def delete_product_size(size_id):
    """Delete a product size (admin only)."""
    logger.info(f"Processing delete product size request for size ID: {size_id}")
    try:
        size = ProductSize.query.get_or_404(size_id)
        size_name = size.name
        
        db.session.delete(size)
        db.session.commit()
        
        logger.info(f"Product size deleted: {size_name}")
        return jsonify({'message': 'Product size deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting product size: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete product size'}), 500

# ---------- SETTINGS MANAGEMENT ----------

@pos_api.route('/admin/settings', methods=['GET'])
@_require_auth(Role.ADMIN)
def get_settings():
    """Get all system settings"""
    try:
        settings = Settings.query.all()
        settings_dict = {setting.key: setting.value for setting in settings}
        
        return jsonify({
            'success': True,
            'settings': [setting.to_dict() for setting in settings]
        })
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@pos_api.route('/settings', methods=['GET'])
@_require_auth()  # Any authenticated user
def get_public_settings():
    """Get settings for POS clients (cashier or admin)."""
    try:
        settings = Settings.query.all()
        return jsonify({setting.key: setting.value for setting in settings}), 200
    except Exception as e:
        logger.error(f"Error getting public settings: {str(e)}")
        return jsonify({'error': 'Failed to get settings'}), 500

@pos_api.route('/admin/settings', methods=['POST'])
@_require_auth(Role.ADMIN)
def save_settings():
    """Save system settings"""
    try:
        data = request.get_json()
        
        for key, value in data.items():
            # Check if setting exists
            setting = Settings.query.filter_by(key=key).first()
            
            if setting:
                # Update existing setting
                setting.value = str(value)
                setting.updated_at = datetime.utcnow()
            else:
                # Create new setting
                setting = Settings(
                    key=key,
                    value=str(value),
                    description=get_setting_description(key)
                )
                db.session.add(setting)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Settings saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

def get_setting_description(key):
    """Get description for setting key"""
    descriptions = {
        'shop-name': 'Coffee shop business name',
        'shop-slogan': 'Coffee shop slogan or tagline',
        'currency-symbol': 'Currency symbol for pricing',
        'primary-color': 'Primary color for the interface',
        'secondary-color': 'Secondary color for the interface',
        'accent-color': 'Accent color for highlights',
        'background-type': 'Type of background (solid, gradient, image)',
        'background-color': 'Background color for solid backgrounds',
        'card-style': 'Style for interface cards',
        'font-family': 'Font family for text',
        'font-size': 'Font size for text',
        'theme-mode': 'Theme mode (light, dark, auto)'
    }
    return descriptions.get(key, 'System setting')

# ---------- PRODUCT MODIFIERS MANAGEMENT ----------

@pos_api.route('/admin/products/<int:product_id>/modifiers', methods=['GET'])
@_require_auth(Role.ADMIN)
def get_product_modifiers(product_id):
    """Get all modifiers for a product (admin only)."""
    logger.info(f"Processing get product modifiers request for product ID: {product_id}")
    try:
        product = Product.query.get_or_404(product_id)
        modifiers = ProductModifier.query.filter_by(product_id=product_id).all()
        
        return jsonify({
            'modifiers': [modifier.to_dict() for modifier in modifiers]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting product modifiers: {str(e)}")
        return jsonify({'error': 'Failed to get product modifiers'}), 500

@pos_api.route('/admin/products/<int:product_id>/modifiers', methods=['POST'])
@_require_auth(Role.ADMIN)
def create_product_modifier(product_id):
    """Create a new modifier for a product (admin only)."""
    logger.info(f"Processing create product modifier request for product ID: {product_id}")
    try:
        data = request.get_json()
        
        if not data or 'name' not in data or 'price_modifier' not in data:
            return jsonify({'error': 'Name and price_modifier are required'}), 400
        
        # Check if product exists
        product = Product.query.get_or_404(product_id)
        
        # Check if modifier name already exists for this product
        existing_modifier = ProductModifier.query.filter_by(
            product_id=product_id, 
            name=data['name']
        ).first()
        
        if existing_modifier:
            return jsonify({'error': 'Modifier with this name already exists for this product'}), 400
        
        modifier = ProductModifier(
            product_id=product_id,
            name=data['name'],
            price_modifier=data['price_modifier']
        )
        
        db.session.add(modifier)
        db.session.commit()
        
        logger.info(f"Product modifier created: {modifier.name} for product {product.name}")
        return jsonify(modifier.to_dict()), 201
        
    except Exception as e:
        logger.error(f"Error creating product modifier: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create product modifier'}), 500

@pos_api.route('/admin/modifiers/<int:modifier_id>', methods=['PUT'])
@_require_auth(Role.ADMIN)
def update_product_modifier(modifier_id):
    """Update a product modifier (admin only)."""
    logger.info(f"Processing update product modifier request for modifier ID: {modifier_id}")
    try:
        modifier = ProductModifier.query.get_or_404(modifier_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'name' in data:
            # Check if another modifier with this name exists for the same product
            existing_modifier = ProductModifier.query.filter(
                ProductModifier.product_id == modifier.product_id,
                ProductModifier.name == data['name'],
                ProductModifier.id != modifier_id
            ).first()
            
            if existing_modifier:
                return jsonify({'error': 'Modifier with this name already exists for this product'}), 400
            
            modifier.name = data['name']
        
        if 'price_modifier' in data:
            modifier.price_modifier = data['price_modifier']
        
        db.session.commit()
        
        logger.info(f"Product modifier updated: {modifier.name}")
        return jsonify(modifier.to_dict()), 200
        
    except Exception as e:
        logger.error(f"Error updating product modifier: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update product modifier'}), 500

@pos_api.route('/admin/modifiers/<int:modifier_id>', methods=['DELETE'])
@_require_auth(Role.ADMIN)
def delete_product_modifier(modifier_id):
    """Delete a product modifier (admin only)."""
    logger.info(f"Processing delete product modifier request for modifier ID: {modifier_id}")
    try:
        modifier = ProductModifier.query.get_or_404(modifier_id)
        modifier_name = modifier.name
        
        db.session.delete(modifier)
        db.session.commit()
        
        logger.info(f"Product modifier deleted: {modifier_name}")
        return jsonify({'message': 'Product modifier deleted successfully'}), 200
        
    except Exception as e:
        logger.error(f"Error deleting product modifier: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete product modifier'}), 500

# ---------- DAILY ANALYTICS RESET ----------
def reset_daily_analytics():
    """Reset daily analytics data (called every midnight)."""
    logger.info("Starting daily analytics reset")
    try:
        # Get today's date
        today = datetime.now().date()
        
        # Mark all completed orders from today as 'archived' for analytics purposes
        # This way they won't show in daily analytics but are still available for PDF reports
        orders_today = Order.query.filter(
            Order.status == 'completed',
            db.func.date(Order.created_at) == today
        ).all()
        
        for order in orders_today:
            # Add a flag to indicate this order was processed in daily reset
            # We'll use the special_instructions field to mark it
            if not order.special_instructions:
                order.special_instructions = f"DAILY_RESET_{today}"
            elif "DAILY_RESET_" not in order.special_instructions:
                order.special_instructions += f"|DAILY_RESET_{today}"
        
        db.session.commit()
        logger.info(f"Daily analytics reset completed. Processed {len(orders_today)} orders.")
        
    except Exception as e:
        logger.error(f"Error during daily analytics reset: {str(e)}")
        db.session.rollback()

def run_scheduler():
    """Run the scheduler in a separate thread."""
    schedule.every().day.at("00:00").do(reset_daily_analytics)
    logger.info("Daily reset scheduler configured for 00:00 every day")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def start_daily_reset_scheduler():
    """Start the daily reset scheduler in a background thread."""
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    logger.info("Daily analytics reset scheduler started")

@pos_api.route('/analytics/reset', methods=['POST'])
@_require_auth(Role.ADMIN)
def manual_reset_analytics():
    """Manually reset daily analytics (admin only)."""
    logger.info("Processing manual analytics reset request")
    try:
        reset_daily_analytics()
        return jsonify({'message': 'Daily analytics reset successfully'}), 200
    except Exception as e:
        logger.error(f"Error in manual analytics reset: {str(e)}")
        return jsonify({'error': 'Failed to reset analytics'}), 500

@pos_api.route('/analytics/scheduler/status', methods=['GET'])
@_require_auth(Role.ADMIN)
def get_scheduler_status():
    """Get scheduler status and next run time (admin only)."""
    try:
        jobs = schedule.get_jobs()
        next_run = None
        if jobs:
            next_run = jobs[0].next_run.isoformat() if jobs[0].next_run else None
        
        return jsonify({
            'scheduler_active': len(jobs) > 0,
            'next_reset': next_run,
            'message': 'Daily reset scheduled for 00:00 every day'
        }), 200
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        return jsonify({'error': 'Failed to get scheduler status'}), 500

def init_pos_app(app):
    """Register the POS API blueprint with the Flask app."""
    app.register_blueprint(pos_api, url_prefix='/api/pos')
    # Start the daily reset scheduler
    start_daily_reset_scheduler()
