from flask import Blueprint, jsonify, request, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta, timezone
from models import db, User, Category, Product, Sale, SaleItem, Role, PaymentMethod, CashRegisterSession, Order
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

api = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

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

# ---------- AUTHENTICATION ----------
@api.route('/login', methods=['POST'])
def login():
    """Authenticate a user and return a JWT token."""
    logger.info("Processing login request")
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        logger.error("Missing username or password in login request")
        return jsonify({'error': 'Username and password required'}), 400

    user = db.session.query(User).filter_by(username=data['username']).first()
    if not user or not check_password_hash(user.password_hash, data['password']):
        logger.error(f"Invalid credentials for username: {data['username']}")
        return jsonify({'error': 'Invalid credentials'}), 401
    if not user.is_active:
        logger.error(f"Inactive user attempted login: {data['username']}")
        return jsonify({'error': 'Account is inactive'}), 401

    token = pyjwt.encode({
        'user_id': user.id,
        'role': user.role.value,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRATION_MINUTES)
    }, SECRET_KEY, algorithm='HS256')

    logger.info(f"Login successful for user: {user.username}")
    return jsonify({
        'message': f'Welcome {user.username}',
        'token': token,
        'user': user.to_dict()
    }), 200

# ---------- USERS ----------
@api.route('/users', methods=['POST'])
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

@api.route('/users', methods=['GET'])
@_require_auth(Role.ADMIN)
def get_users():
    """Retrieve all active users (admin only)."""
    logger.info("Processing get users request")
    users = db.session.query(User).filter_by(is_active=True).all()
    return jsonify([user.to_dict() for user in users]), 200

# ---------- CATEGORIES ----------
@api.route('/categories', methods=['POST'])
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

@api.route('/categories/<int:category_id>', methods=['PUT'])
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

@api.route('/categories', methods=['GET'])
@_require_auth()
def get_categories():
    """Retrieve all active categories with product counts."""
    logger.info("Processing get categories request")
    categories = db.session.query(Category).filter_by(is_active=True).all()
    
    # Add product count for each category
    categories_with_counts = []
    for category in categories:
        category_dict = category.to_dict()
        product_count = db.session.query(Product).filter(Product.category_id == category.id).count()
        category_dict['product_count'] = product_count
        categories_with_counts.append(category_dict)
    
    return jsonify(categories_with_counts), 200

# ---------- PRODUCTS ----------
@api.route('/products', methods=['POST'])
@_require_auth(Role.ADMIN)
def create_product():
    """Create a new product (admin only)."""
    logger.info("Processing create product request")
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'price', 'stock', 'category_id']):
        logger.error("Missing required fields in create product request")
        return jsonify({'error': 'Name, price, stock, and category_id required'}), 400

    if not isinstance(data['price'], int):
        logger.error(f"Invalid price type: {data['price']} (must be integer)")
        return jsonify({'error': 'Price must be an integer'}), 400

    if data['stock'] < 0:
        logger.error(f"Invalid stock value: {data['stock']}")
        return jsonify({'error': 'Stock cannot be negative'}), 400

    try:
        product = Product(
            name=data['name'],
            price=data['price'],
            stock=data['stock'],
            category_id=data['category_id'],
            description=data.get('description', '')
        )
        db.session.add(product)
        db.session.commit()
        logger.info(f"Product created: {product.name}")
        return jsonify(product.to_dict()), 201
    except IntegrityError:
        db.session.rollback()
        logger.error(f"Product name already exists: {data['name']}")
        return jsonify({'error': 'Product name already exists'}), 400

@api.route('/products', methods=['GET'])
@_require_auth()
def get_products():
    """Retrieve all active products."""
    logger.info("Processing get products request")
    products = db.session.query(Product).filter_by(is_active=True).options(selectinload(Product.category)).all()
    return jsonify([product.to_dict() for product in products]), 200

# ---------- SALES ----------
@api.route('/sales', methods=['POST'])
@_require_auth(Role.CASHIER)
def create_sale():
    """Create a new sale (cashier only)."""
    logger.info("Processing create sale request")
    data = request.get_json()
    if not data or not all(k in data for k in ['items', 'payment_method']):
        logger.error("Missing required fields in create sale request")
        return jsonify({'error': 'Items and payment_method required'}), 400

    try:
        payment_method = PaymentMethod[data['payment_method'].upper()]
    except KeyError:
        logger.error(f"Invalid payment_method: {data['payment_method']}")
        return jsonify({'error': 'Invalid payment method'}), 400

    session = db.session.query(CashRegisterSession).filter_by(
        user_id=request.user.id, status='open').first()
    if not session:
        logger.error("No open cash register session found")
        return jsonify({'error': 'No open cash register session'}), 400

    total = 0
    sale_items = []
    for item in data['items']:
        product = db.session.get(Product, item['product_id'])
        if not product:
            logger.error(f"Product not found: ID={item['product_id']}")
            return jsonify({'error': f'Product ID {item["product_id"]} not found'}), 404
        if item['quantity'] <= 0:
            logger.error(f"Invalid quantity: {item['quantity']}")
            return jsonify({'error': 'Quantity must be positive'}), 400
        if product.stock < item['quantity']:
            logger.error(f"Insufficient stock for product: {product.name}")
            return jsonify({'error': f'Insufficient stock for {product.name}'}), 400

        total += product.price * item['quantity']
        sale_items.append(SaleItem(
            product_id=product.id,
            quantity=item['quantity'],
            unit_price=product.price
        ))
        product.stock -= item['quantity']

    sale = Sale(
        total=total,
        payment_method=payment_method,
        user_id=request.user.id,
        session_id=session.id
    )
    sale.items = sale_items
    db.session.add(sale)
    try:
        db.session.commit()
        logger.info(f"Sale created: ID={sale.id}, Total={total}")
        return jsonify(sale.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating sale: {str(e)}")
        return jsonify({'error': 'Failed to create sale'}), 400

@api.route('/sales', methods=['GET'])
@_require_auth()
def get_sales():
    """Retrieve sales with optional filters."""
    logger.info("Processing get sales request")
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id', type=int)
    category_id = request.args.get('category_id', type=int)
    product_id = request.args.get('product_id', type=int)
    format = request.args.get('format', 'json')

    if user_id and not isinstance(user_id, int):
        logger.error("Invalid user_id: must be integer")
        return jsonify({'error': 'User ID must be an integer'}), 400
    if category_id and not isinstance(category_id, int):
        logger.error("Invalid category_id: must be integer")
        return jsonify({'error': 'Category ID must be an integer'}), 400
    if product_id and not isinstance(product_id, int):
        logger.error("Invalid product_id: must be integer")
        return jsonify({'error': 'Product ID must be an integer'}), 400
    if user_id and (request.user.role != Role.ADMIN and request.user.id != user_id):
        logger.error("Non-admin user attempted to access other users' data")
        return jsonify({'error': 'Cannot access other users’ data'}), 403

    query = db.session.query(Sale).filter_by(is_active=True)
    if user_id:
        query = query.filter_by(user_id=user_id)
    try:
        if start_date:
            query = query.filter(Sale.date >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Sale.date <= datetime.fromisoformat(end_date))
    except ValueError:
        logger.error("Invalid date format in get sales request")
        return jsonify({'error': 'Invalid date format (use ISO format)'}), 400
    if category_id:
        category = db.session.get(Category, category_id)
        if not category:
            logger.error(f"Category not found: ID={category_id}")
            return jsonify({'error': 'Category not found'}), 404
        query = query.join(SaleItem).join(Product).filter(Product.category_id == category_id)
    if product_id:
        query = query.join(SaleItem).filter(SaleItem.product_id == product_id)

    sales = query.all()
    total_sales = sum(s.total for s in sales)

    if format == 'pdf':
        table_data = [['ID', 'Date', 'User', 'Total', 'Items']] + [
            [s.id, s.date.strftime('%Y-%m-%d %H:%M'), s.user.username, f"{s.total}",
             ", ".join(f"{item.quantity}x {item.product.name}" for item in s.items)]
            for s in sales
        ]
        pdf = _generate_pdf("Sales Report", {'table': table_data, 'total': f"{total_sales}"})
        logger.info("Generated PDF sales report")
        return Response(pdf, mimetype="application/pdf",
                        headers={"Content-Disposition": "attachment;filename=sales_report.pdf"})

    logger.info(f"Retrieved {len(sales)} sales")
    return jsonify({
        'sales': [{
            **s.to_dict(),
            'items': [{
                **item.to_dict(),
                'product_name': item.product.name
            } for item in s.items],
            'user_name': s.user.username
        } for s in sales],
        'total': total_sales
    }), 200

# ---------- DASHBOARD STATISTICS ----------
@api.route('/dashboard/stats', methods=['GET'])
@_require_auth()
def get_dashboard_stats():
    """Get dashboard statistics including today's sales and orders."""
    logger.info("Processing get dashboard stats request")
    
    try:
        # Get today's date range
        today = datetime.now(timezone.utc).date()
        start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Get today's completed orders
        today_orders = db.session.query(Order).filter(
            Order.status == 'completed',
            Order.completed_at >= start_of_day,
            Order.completed_at <= end_of_day
        ).all()
        
        # Calculate today's statistics
        today_sales = sum(order.total for order in today_orders)
        today_orders_count = len(today_orders)
        
        # Get total products count
        total_products = db.session.query(Product).count()
        
        # Get low stock products count
        low_stock_products = db.session.query(Product).filter(
            Product.stock <= Product.low_stock_threshold
        ).count()
        
        logger.info(f"Dashboard stats - Today's sales: {today_sales}, Orders: {today_orders_count}")
        
        return jsonify({
            'today_sales': today_sales,
            'today_orders': today_orders_count,
            'total_products': total_products,
            'low_stock_count': low_stock_products
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({'error': 'Failed to get dashboard statistics'}), 500

# ---------- CASH REGISTER SESSIONS ----------
@api.route('/cash-register-sessions', methods=['POST'])
@_require_auth(Role.CASHIER)
def open_cash_register_session():
    """Open a new cash register session (cashier only)."""
    logger.info("Processing open cash register session request")
    data = request.get_json()
    if not data or 'starting_cash' not in data:
        logger.error("Missing starting_cash in open session request")
        return jsonify({'error': 'Starting cash required'}), 400

    if not isinstance(data['starting_cash'], int) or data['starting_cash'] < 0:
        logger.error(f"Invalid starting_cash: {data['starting_cash']}")
        return jsonify({'error': 'Starting cash must be a non-negative integer'}), 400

    existing_session = db.session.query(CashRegisterSession).filter_by(
        user_id=request.user.id, status='open').first()
    if existing_session:
        logger.error(f"User already has an open session: ID={existing_session.id}")
        return jsonify({'error': 'User already has an open session'}), 400

    session = CashRegisterSession(
        user_id=request.user.id,
        starting_cash=data['starting_cash']
    )
    db.session.add(session)
    db.session.commit()
    logger.info(f"Cash register session opened: ID={session.id}")
    return jsonify(session.to_dict()), 201

@api.route('/cash-register-sessions/<int:session_id>/close', methods=['PUT'])
@_require_auth(Role.CASHIER)
def close_cash_register_session(session_id):
    """Close a cash register session (cashier only)."""
    logger.info(f"Processing close cash register session request for ID: {session_id}")
    session = db.session.get(CashRegisterSession, session_id)
    if not session:
        logger.error(f"Session not found: ID={session_id}")
        return jsonify({'error': 'Session not found'}), 404
    if session.user_id != request.user.id:
        logger.error(f"Unauthorized attempt to close session: ID={session_id}")
        return jsonify({'error': 'Not authorized to close this session'}), 403
    if session.status == 'closed':
        logger.error(f"Session already closed: ID={session_id}")
        return jsonify({'error': 'Session already closed'}), 400

    data = request.get_json()
    if not data or 'ending_cash' not in data:
        logger.error("Missing ending_cash in close session request")
        return jsonify({'error': 'Ending cash required'}), 400
    if not isinstance(data['ending_cash'], int) or data['ending_cash'] < 0:
        logger.error(f"Invalid ending_cash: {data['ending_cash']}")
        return jsonify({'error': 'Ending cash must be a non-negative integer'}), 400

    session.ending_cash = data['ending_cash']
    session.status = 'closed'
    session.end_time = datetime.now(timezone.utc)
    db.session.commit()
    logger.info(f"Cash register session closed: ID={session.id}")
    return jsonify(session.to_dict()), 200

# ---------- UTILS ----------
def _generate_pdf(title, data):
    """Generate a PDF report."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(title, styles['Title']))
    table = Table(data['table'])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Paragraph(f"Total: {data['total']}", styles['Normal']))
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

def init_app(app):
    """Register the API blueprint with the Flask app."""
    app.register_blueprint(api, url_prefix='/api')