from flask_sqlalchemy import SQLAlchemy
from enum import Enum
from datetime import datetime, timezone

db = SQLAlchemy()

class Role(Enum):
    ADMIN = 'admin'
    CASHIER = 'cashier'

class PaymentMethod(Enum):
    CASH = 'cash'
    CREDIT_CARD = 'credit_card'
    MOBILE = 'mobile'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    sales = db.relationship('Sale', back_populates='user')
    sessions = db.relationship('CashRegisterSession', back_populates='user')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, default='')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    products = db.relationship('Product', back_populates='category')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    description = db.Column(db.Text, default='')
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Ajouté
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.CheckConstraint('price > 0', name='check_price_positive'),
        db.CheckConstraint('stock >= 0', name='check_stock_non_negative'),
    )
    
    category = db.relationship('Category', back_populates='products')
    sale_items = db.relationship('SaleItem', back_populates='product')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'stock': self.stock,
            'category_id': self.category_id,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_register_sessions.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.CheckConstraint('total > 0', name='check_total_positive'),
    )
    
    user = db.relationship('User', back_populates='sales')
    session = db.relationship('CashRegisterSession', back_populates='sales')
    items = db.relationship('SaleItem', back_populates='sale', cascade='all, delete-orphan')  # Corrigé pour selectinload

    def to_dict(self):
        return {
            'id': self.id,
            'total': self.total,
            'payment_method': self.payment_method.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'is_active': self.is_active,
            'date': self.date.isoformat()
        }

class SaleItem(db.Model):
    __tablename__ = 'sale_items'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='check_quantity_positive'),
        db.CheckConstraint('unit_price > 0', name='check_unit_price_positive'),
    )
    
    sale = db.relationship('Sale', back_populates='items')
    product = db.relationship('Product', back_populates='sale_items')

    def to_dict(self):
        return {
            'id': self.id,
            'sale_id': self.sale_id,
            'product_id': self.product_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price
        }

class CashRegisterSession(db.Model):
    __tablename__ = 'cash_register_sessions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    starting_cash = db.Column(db.Integer, nullable=False)
    ending_cash = db.Column(db.Integer)
    status = db.Column(db.String(20), default='open', nullable=False)
    start_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = db.Column(db.DateTime)
    
    __table_args__ = (
        db.CheckConstraint('starting_cash >= 0', name='check_starting_cash_non_negative'),
        db.CheckConstraint("status IN ('open', 'closed')", name='check_status_valid'),
    )
    
    user = db.relationship('User', back_populates='sessions')
    sales = db.relationship('Sale', back_populates='session')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'starting_cash': self.starting_cash,
            'ending_cash': self.ending_cash,
            'status': self.status,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None
        }