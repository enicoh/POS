import unittest
import logging
from datetime import datetime, timezone
from flask import json
from app import create_app, db
from models import User, Category, Product, Sale, SaleItem, CashRegisterSession, Role, PaymentMethod
from werkzeug.security import generate_password_hash
from config import TestConfig
from sqlalchemy import inspect

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class POSTestCase(unittest.TestCase):
    def setUp(self):
        """Initialisation avant chaque test."""
        logger.info("Début de la configuration du test")
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

        # Créer un utilisateur admin
        self.admin = User(
            username="admin",
            password_hash=generate_password_hash("adminpass"),
            role=Role.ADMIN
        )
        db.session.add(self.admin)
        db.session.commit()
        logger.info("Utilisateur admin créé : %s", self.admin.username)

        # Créer un caissier
        self.cashier = User(
            username="cashier",
            password_hash=generate_password_hash("cashierpass"),
            role=Role.CASHIER
        )
        db.session.add(self.cashier)
        db.session.commit()
        logger.info("Utilisateur caissier créé : %s", self.cashier.username)

        # Obtenir les tokens
        response = self.client.post('/api/login', json={
            'username': 'admin', 'password': 'adminpass'
        })
        self.admin_token = response.json.get('token')
        logger.info("Token admin généré : %s", self.admin_token if self.admin_token else "Échec")

        response = self.client.post('/api/login', json={
            'username': 'cashier', 'password': 'cashierpass'
        })
        self.cashier_token = response.json.get('token')
        logger.info("Token caissier généré : %s", self.cashier_token if self.cashier_token else "Échec")

    def tearDown(self):
        """Nettoyage après chaque test."""
        logger.info("Nettoyage après le test")
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        self.app_context.pop()

    def test_app_runs(self):
        """Test que l'application démarre correctement."""
        logger.info("Début du test : test_app_runs")
        try:
            self.assertIsNotNone(self.app)
            self.assertTrue(self.app.config['TESTING'])
            logger.info("Résultat test_app_runs : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_app_runs : %s", str(e))
            raise

    def test_database_connection(self):
        """Test de connexion à la base de données."""
        logger.info("Début du test : test_database_connection")
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            expected_tables = ['users', 'categories', 'products', 'sales', 'sale_items', 'cash_register_sessions']
            for table in expected_tables:
                self.assertIn(table, tables)
            logger.info("Résultat test_database_connection : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_database_connection : %s", str(e))
            raise

    def test_login_success(self):
        """Test de connexion réussie."""
        logger.info("Début du test : test_login_success")
        try:
            response = self.client.post('/api/login', json={
                'username': 'admin', 'password': 'adminpass'
            })
            self.assertEqual(response.status_code, 200)
            self.assertIn('token', response.json)
            logger.info("Résultat test_login_success : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_login_success : %s", str(e))
            raise

    def test_login_invalid_credentials(self):
        """Test de connexion avec des identifiants invalides."""
        logger.info("Début du test : test_login_invalid_credentials")
        try:
            response = self.client.post('/api/login', json={
                'username': 'admin', 'password': 'wrongpass'
            })
            self.assertEqual(response.status_code, 401)
            logger.info("Résultat test_login_invalid_credentials : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_login_invalid_credentials : %s", str(e))
            raise

    def test_login_missing_fields(self):
        """Test de connexion avec des champs manquants."""
        logger.info("Début du test : test_login_missing_fields")
        try:
            response = self.client.post('/api/login', json={})
            self.assertEqual(response.status_code, 400)
            logger.info("Résultat test_login_missing_fields : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_login_missing_fields : %s", str(e))
            raise

    def test_create_user_as_admin(self):
        """Test de création d'utilisateur par un admin."""
        logger.info("Début du test : test_create_user_as_admin")
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            user_data = {
                "username": "newuser",
                "password": "newpass",
                "role": "cashier"
            }
            response = self.client.post("/api/users", json=user_data, headers=headers)
            self.assertEqual(response.status_code, 201)
            logger.info("Résultat test_create_user_as_admin : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_create_user_as_admin : %s", str(e))
            raise

    def test_create_user_as_cashier_forbidden(self):
        """Test de création d'utilisateur par un caissier (interdit)."""
        logger.info("Début du test : test_create_user_as_cashier_forbidden")
        try:
            headers = {"Authorization": f"Bearer {self.cashier_token}"}
            user_data = {
                "username": "newuser",
                "password": "newpass",
                "role": "cashier"
            }
            response = self.client.post("/api/users", json=user_data, headers=headers)
            self.assertEqual(response.status_code, 403)
            logger.info("Résultat test_create_user_as_cashier_forbidden : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_create_user_as_cashier_forbidden : %s", str(e))
            raise

    def test_create_user_invalid_username(self):
        """Test de création d'utilisateur avec nom d'utilisateur invalide."""
        logger.info("Début du test : test_create_user_invalid_username")
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            user_data = {
                "username": "a!",  # Nom d'utilisateur invalide
                "password": "newpass",
                "role": "cashier"
            }
            response = self.client.post("/api/users", json=user_data, headers=headers)
            self.assertEqual(response.status_code, 400)
            logger.info("Résultat test_create_user_invalid_username : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_create_user_invalid_username : %s", str(e))
            raise

    def test_user_model_basic(self):
        """Test basique du modèle User."""
        logger.info("Début du test : test_user_model_basic")
        try:
            user = User(
                username="testuser",
                password_hash=generate_password_hash("testpass"),
                role=Role.CASHIER
            )
            db.session.add(user)
            db.session.commit()
            self.assertEqual(user.username, "testuser")
            self.assertEqual(user.role, Role.CASHIER)
            logger.info("Résultat test_user_model_basic : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_user_model_basic : %s", str(e))
            raise

    def test_create_category_as_admin(self):
        """Test de création de catégorie par un admin."""
        logger.info("Début du test : test_create_category_as_admin")
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            category_data = {
                "name": "Test Category",
                "description": "A test category"
            }
            response = self.client.post("/api/categories", json=category_data, headers=headers)
            self.assertEqual(response.status_code, 201)
            logger.info("Résultat test_create_category_as_admin : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_create_category_as_admin : %s", str(e))
            raise

    def test_update_category(self):
        """Test de mise à jour de catégorie."""
        logger.info("Début du test : test_update_category")
        try:
            category = Category(name="Old Category", description="Old")
            db.session.add(category)
            db.session.commit()
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            category_data = {
                "name": "New Category",
                "description": "Updated"
            }
            response = self.client.put(f"/api/categories/{category.id}", json=category_data, headers=headers)
            self.assertEqual(response.status_code, 200)
            logger.info("Résultat test_update_category : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_update_category : %s", str(e))
            raise

    def test_get_categories(self):
        """Test de récupération des catégories."""
        logger.info("Début du test : test_get_categories")
        try:
            category = Category(name="Test Category", description="Test")
            db.session.add(category)
            db.session.commit()
            
            headers = {"Authorization": f"Bearer {self.cashier_token}"}
            response = self.client.get("/api/categories", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json), 1)
            logger.info("Résultat test_get_categories : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_get_categories : %s", str(e))
            raise

    def test_create_product_as_admin(self):
        """Test de création de produit par un admin."""
        logger.info("Début du test : test_create_product_as_admin")
        try:
            category = Category(name="Test Category", description="Test")
            db.session.add(category)
            db.session.commit()
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            product_data = {
                "name": "Test Product",
                "price": 100,
                "stock": 10,
                "category_id": category.id,
                "description": "Test"
            }
            response = self.client.post("/api/products", json=product_data, headers=headers)
            self.assertEqual(response.status_code, 201)
            logger.info("Résultat test_create_product_as_admin : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_create_product_as_admin : %s", str(e))
            raise

    def test_create_product_invalid_price(self):
        """Test de création de produit avec prix invalide."""
        logger.info("Début du test : test_create_product_invalid_price")
        try:
            category = Category(name="Test Category", description="Test")
            db.session.add(category)
            db.session.commit()
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            product_data = {
                "name": "Test Product",
                "price": -100,  # Prix négatif
                "stock": 10,
                "category_id": category.id
            }
            response = self.client.post("/api/products", json=product_data, headers=headers)
            self.assertEqual(response.status_code, 400)
            logger.info("Résultat test_create_product_invalid_price : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_create_product_invalid_price : %s", str(e))
            raise

    def test_price_type_handling(self):
        """Test diagnostic pour les types de prix."""
        logger.info("Début du test : test_price_type_handling")
        try:
            category = Category(name="Test Category", description="Test")
            db.session.add(category)
            db.session.commit()
            
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            product_data = {
                "name": "Test Product",
                "price": 2.99,  # Prix flottant
                "stock": 10,
                "category_id": category.id
            }
            response = self.client.post("/api/products", json=product_data, headers=headers)
            self.assertEqual(response.status_code, 400)  # Attendu car price doit être int
            logger.info("Résultat test_price_type_handling : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_price_type_handling : %s", str(e))
            raise

    def test_get_products(self):
        """Test de récupération des produits."""
        logger.info("Début du test : test_get_products")
        try:
            category = Category(name="Test Category", description="Test")
            db.session.add(category)
            db.session.commit()
            
            product = Product(name="Test Product", price=100, stock=10, category_id=category.id)
            db.session.add(product)
            db.session.commit()
            
            headers = {"Authorization": f"Bearer {self.cashier_token}"}
            response = self.client.get("/api/products", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json), 1)
            logger.info("Résultat test_get_products : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_get_products : %s", str(e))
            raise

    def test_create_sale_basic(self):
        """Test de création d'une vente basique."""
        logger.info("Début du test : test_create_sale_basic")
        try:
            category = Category(name="Test Category", description="Test")
            db.session.add(category)
            db.session.commit()
            
            product = Product(name="Test Product", price=500, stock=10, category_id=category.id)
            db.session.add(product)
            db.session.commit()
            
            session = CashRegisterSession(user_id=self.cashier.id, starting_cash=100)
            db.session.add(session)
            db.session.commit()
            
            sale_data = {
                "items": [{"product_id": product.id, "quantity": 2}],
                "payment_method": "cash"
            }
            headers = {"Authorization": f"Bearer {self.cashier_token}"}
            response = self.client.post("/api/sales", json=sale_data, headers=headers)
            self.assertEqual(response.status_code, 201)
            logger.info("Résultat test_create_sale_basic : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_create_sale_basic : %s", str(e))
            raise

    def test_get_sales(self):
        """Test de récupération des ventes."""
        logger.info("Début du test : test_get_sales")
        try:
            category = Category(name="Test Category", description="Test")
            db.session.add(category)
            db.session.commit()
            
            product = Product(name="Test Product", price=500, stock=10, category_id=category.id)
            db.session.add(product)
            db.session.commit()
            
            session = CashRegisterSession(user_id=self.cashier.id, starting_cash=100)
            db.session.add(session)
            db.session.commit()
            
            sale = Sale(total=1000, payment_method=PaymentMethod.CASH, user_id=self.cashier.id, session_id=session.id)
            sale_item = SaleItem(sale=sale, product_id=product.id, quantity=2, unit_price=500)
            db.session.add_all([sale, sale_item])
            db.session.commit()
            
            headers = {"Authorization": f"Bearer {self.cashier_token}"}
            response = self.client.get("/api/sales", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json['sales']), 1)
            logger.info("Résultat test_get_sales : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_get_sales : %s", str(e))
            raise

    def test_open_cash_register_session(self):
        """Test d'ouverture de session de caisse."""
        logger.info("Début du test : test_open_cash_register_session")
        try:
            headers = {"Authorization": f"Bearer {self.cashier_token}"}
            session_data = {"starting_cash": 100}
            response = self.client.post("/api/cash-register-sessions", json=session_data, headers=headers)
            self.assertEqual(response.status_code, 201)
            logger.info("Résultat test_open_cash_register_session : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_open_cash_register_session : %s", str(e))
            raise

    def test_close_cash_register_session(self):
        """Test de fermeture de session de caisse."""
        logger.info("Début du test : test_close_cash_register_session")
        try:
            session = CashRegisterSession(user_id=self.cashier.id, starting_cash=100)
            db.session.add(session)
            db.session.commit()
            
            headers = {"Authorization": f"Bearer {self.cashier_token}"}
            response = self.client.put(f"/api/cash-register-sessions/{session.id}/close", json={"ending_cash": 150}, headers=headers)
            self.assertEqual(response.status_code, 200)
            logger.info("Résultat test_close_cash_register_session : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_close_cash_register_session : %s", str(e))
            raise

    def test_invalid_token(self):
        """Test avec token invalide."""
        logger.info("Début du test : test_invalid_token")
        try:
            headers = {"Authorization": "Bearer invalidtoken"}
            response = self.client.get("/api/users", headers=headers)
            self.assertEqual(response.status_code, 401)
            logger.info("Résultat test_invalid_token : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_invalid_token : %s", str(e))
            raise

    def test_unauthorized_access(self):
        """Test d'accès non autorisé."""
        logger.info("Début du test : test_unauthorized_access")
        try:
            response = self.client.get("/api/users")
            self.assertEqual(response.status_code, 401)
            logger.info("Résultat test_unauthorized_access : SUCCÈS")
        except Exception as e:
            logger.error("Erreur dans test_unauthorized_access : %s", str(e))
            raise

if __name__ == '__main__':
    unittest.main(verbosity=2)