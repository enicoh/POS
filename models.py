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

class OrderType(Enum):
    DINE_IN = 'dine_in'
    TAKEAWAY = 'takeaway'

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
    image_url = db.Column(db.String(255), default='')
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    low_stock_threshold = db.Column(db.Integer, default=10, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.CheckConstraint('price > 0', name='check_price_positive'),
        db.CheckConstraint('stock >= 0', name='check_stock_non_negative'),
        db.CheckConstraint('low_stock_threshold >= 0', name='check_low_stock_threshold_non_negative'),
    )
    
    category = db.relationship('Category', back_populates='products')
    sale_items = db.relationship('SaleItem', back_populates='product')
    sizes = db.relationship('ProductSize', back_populates='product', cascade='all, delete-orphan')
    modifiers = db.relationship('ProductModifier', back_populates='product', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'stock': self.stock,
            'category_id': self.category_id,
            'description': self.description,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'low_stock_threshold': self.low_stock_threshold,
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

class ProductSize(db.Model):
    __tablename__ = 'product_sizes'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Small", "Medium", "Large"
    price_modifier = db.Column(db.Integer, default=0, nullable=False)  # Additional cost for this size
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    product = db.relationship('Product', back_populates='sizes')
    order_items = db.relationship('OrderItem', back_populates='size')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'name': self.name,
            'price_modifier': self.price_modifier,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class ProductModifier(db.Model):
    __tablename__ = 'product_modifiers'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Extra Shot", "Decaf", "Oat Milk"
    price_modifier = db.Column(db.Integer, default=0, nullable=False)  # Additional cost for this modifier
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    product = db.relationship('Product', back_populates='modifiers')
    order_item_modifiers = db.relationship('OrderItemModifier', back_populates='modifier')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'name': self.name,
            'price_modifier': self.price_modifier,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('cash_register_sessions.id'), nullable=False)
    customer_name = db.Column(db.String(100), default='')
    customer_phone = db.Column(db.String(20), default='')
    order_type = db.Column(db.Enum(OrderType), default=OrderType.TAKEAWAY, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, completed, cancelled
    subtotal = db.Column(db.Integer, default=0, nullable=False)
    tax_amount = db.Column(db.Integer, default=0, nullable=False)
    total = db.Column(db.Integer, default=0, nullable=False)
    notes = db.Column(db.Text, default='')
    special_instructions = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.CheckConstraint("status IN ('pending', 'completed', 'cancelled')", name='check_order_status_valid'),
        db.CheckConstraint('subtotal >= 0', name='check_subtotal_non_negative'),
        db.CheckConstraint('tax_amount >= 0', name='check_tax_amount_non_negative'),
        db.CheckConstraint('total >= 0', name='check_total_non_negative'),
    )
    
    user = db.relationship('User')
    session = db.relationship('CashRegisterSession')
    items = db.relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    payment = db.relationship('Payment', back_populates='order', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'order_type': self.order_type.value,
            'status': self.status,
            'subtotal': self.subtotal,
            'tax_amount': self.tax_amount,
            'total': self.total,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'items': [item.to_dict() for item in self.items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size_id = db.Column(db.Integer, db.ForeignKey('product_sizes.id'))
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Integer, nullable=False)
    special_instructions = db.Column(db.Text, default='')
    
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='check_quantity_positive'),
        db.CheckConstraint('unit_price >= 0', name='check_unit_price_non_negative'),
        db.CheckConstraint('total_price >= 0', name='check_total_price_non_negative'),
    )
    
    order = db.relationship('Order', back_populates='items')
    product = db.relationship('Product')
    size = db.relationship('ProductSize', back_populates='order_items')
    modifiers = db.relationship('OrderItemModifier', back_populates='order_item', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'product_id': self.product_id,
            'size_id': self.size_id,
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'special_instructions': self.special_instructions,
            'product_name': self.product.name if self.product else 'Unknown Product',
            'size_name': self.size.name if self.size else None,
            'modifier_ids': [mod.modifier_id for mod in self.modifiers],
            'modifiers': [{'id': mod.modifier_id, 'name': mod.modifier.name, 'price_modifier': mod.price_modifier} for mod in self.modifiers]
        }

class OrderItemModifier(db.Model):
    __tablename__ = 'order_item_modifiers'
    id = db.Column(db.Integer, primary_key=True)
    order_item_id = db.Column(db.Integer, db.ForeignKey('order_items.id'), nullable=False)
    modifier_id = db.Column(db.Integer, db.ForeignKey('product_modifiers.id'), nullable=False)
    price_modifier = db.Column(db.Integer, nullable=False)
    
    order_item = db.relationship('OrderItem', back_populates='modifiers')
    modifier = db.relationship('ProductModifier', back_populates='order_item_modifiers')

    def to_dict(self):
        return {
            'id': self.id,
            'order_item_id': self.order_item_id,
            'modifier_id': self.modifier_id,
            'price_modifier': self.price_modifier
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    payment_method = db.Column(db.Enum(PaymentMethod), nullable=False)
    transaction_id = db.Column(db.String(100), default='')
    status = db.Column(db.String(20), default='completed', nullable=False)  # pending, completed, failed, refunded
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='check_amount_positive'),
        db.CheckConstraint("status IN ('pending', 'completed', 'failed', 'refunded')", name='check_payment_status_valid'),
    )
    
    order = db.relationship('Order', back_populates='payment')

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'amount': self.amount,
            'payment_method': self.payment_method.value,
            'transaction_id': self.transaction_id,
            'status': self.status,
            'created_at': self.created_at.isoformat()
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

class Settings(db.Model):
    __tablename__ = 'settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }