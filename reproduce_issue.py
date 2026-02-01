from app import create_app
from models import db, User, Role, Product, ProductSize, ProductModifier, CashRegisterSession, Category
from werkzeug.security import generate_password_hash
import jwt as pyjwt
from datetime import datetime, timedelta, timezone

app = create_app()

with app.app_context():
    print("Setting up test data...")
    # 1. Get/Create Cashier
    cashier = db.session.query(User).filter_by(username='cashier_test').first()
    if not cashier:
        cashier = User(username='cashier_test', password_hash=generate_password_hash('password'), role=Role.CASHIER)
        db.session.add(cashier)
        db.session.commit()
        print("Created cashier user")
    
    # 2. Get/Create Category
    cat = db.session.query(Category).first()
    if not cat:
        cat = Category(name='Test Category')
        db.session.add(cat)
        db.session.commit()
        print("Created category")

    # 3. Get/Create Product with options
    product = db.session.query(Product).filter_by(name='Test Product').first()
    size = None
    mod = None
    
    if not product:
        product = Product(name='Test Product', price=100, stock=100, category_id=cat.id)
        db.session.add(product)
        db.session.flush()
        
        size = ProductSize(product_id=product.id, name='Large', price_modifier=50)
        mod = ProductModifier(product_id=product.id, name='Sauce', price_modifier=20)
        db.session.add(size)
        db.session.add(mod)
        db.session.commit()
        print("Created product with options")
    else:
        # Ensure it has sizes/mods
        if not product.sizes:
            size = ProductSize(product_id=product.id, name='Large', price_modifier=50)
            db.session.add(size)
        else:
            size = product.sizes[0]
            
        if not product.modifiers:
            mod = ProductModifier(product_id=product.id, name='Sauce', price_modifier=20)
            db.session.add(mod)
        else:
            mod = product.modifiers[0]
        db.session.commit()
    
    # Reload to be sure
    db.session.refresh(product)
    
    # 4. Create Session
    session = db.session.query(CashRegisterSession).filter_by(user_id=cashier.id, status='open').first()
    if not session:
        session = CashRegisterSession(user_id=cashier.id, starting_cash=0)
        db.session.add(session)
        db.session.commit()
        print("Created session")

    # 5. Generate Token
    token = pyjwt.encode({
        'user_id': cashier.id,
        'exp': datetime.now(timezone.utc) + timedelta(minutes=60)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    # 6. Make Request
    print("Making API request...")
    with app.test_client() as client:
        headers = {'Authorization': f'Bearer {token}'}
        data = {
            'items': [{
                'product_id': product.id,
                'quantity': 1,
                'size_id': size.id if size else None,
                'modifier_ids': [mod.id] if mod else []
            }],
            'customer_name': 'Test Customer'
        }
        print(f"Sending data: {data}")
        try:
            response = client.post('/api/pos/pos/orders', json=data, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.get_json()}")
        except Exception as e:
            print(f"Exception during request: {e}")
