# API de Point de Vente (POS)

Ce projet est une API RESTful basée sur Flask pour un système de point de vente, conçue pour gérer les utilisateurs, les catégories, les produits, les ventes et les sessions de caisse. Elle utilise JWT pour l'authentification, SQLAlchemy pour les opérations sur la base de données, et prend en charge PostgreSQL ou SQLite. L'API est sécurisée avec un contrôle d'accès basé sur les rôles (Admin et Caissier) et inclut des tests complets ainsi qu'un système de journalisation.

## Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Exécution de l'application](#exécution-de-lapplication)
- [Gestion des migrations de base de données](#gestion-des-migrations-de-base-de-données)
- [Tests](#tests)
- [Endpoints de l'API](#endpoints-de-lapi)
- [Journalisation](#journalisation)
- [Structure du projet](#structure-du-projet)
- [Variables d'environnement](#variables-denvironnement)
- [Exemple d'utilisation](#exemple-dutilisation)
- [Contribution](#contribution)
- [Licence](#licence)

## Fonctionnalités

- **Authentification** : Authentification basée sur JWT avec contrôle d'accès par rôle (Admin et Caissier).
- **Gestion des utilisateurs** : Création et liste des utilisateurs (réservé aux Admins).
- **Gestion des catégories** : Création et mise à jour des catégories (réservé aux Admins).
- **Gestion des produits** : Création et liste des produits avec gestion des stocks et association aux catégories (réservé aux Admins).
- **Gestion des ventes** : Création de ventes et génération de rapports au format JSON ou PDF (Caissiers pour la création, tous les rôles pour la récupération avec restrictions).
- **Sessions de caisse** : Ouverture et fermeture des sessions de caisse (réservé aux Caissiers).
- **Base de données** : Prise en charge de SQLite (développement) et PostgreSQL (production) avec migrations via Flask-Migrate.
- **Journalisation** : Journalisation détaillée dans `app.log` et sur la console.
- **Tests** : Suite de tests unitaires complète avec `unittest` couvrant tous les endpoints et cas limites.
- **CORS** : Gestion configurable des requêtes cross-origin pour l'intégration avec un frontend.

## Prérequis

- Python 3.8 ou supérieur
- PostgreSQL (recommandé pour la production) ou SQLite (pour le développement/tests)
- pip pour l'installation des dépendances

## Installation

1. **Cloner le dépôt** :

   ```bash
   git clone https://github.com/Mazdiou/pos_api.git
   cd pos-api
   ```

2. **Créer un environnement virtuel** :

   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows : venv\Scripts\activate
   ```

3. **Installer les dépendances** :

   ```bash
   pip install -r requirements.txt
   ```

   Le fichier `requirements.txt` inclut :

   - Flask==3.1.2
   - Flask-SQLAlchemy==3.1.1
   - Flask-JWT-Extended==4.7.1
   - Flask-Migrate==4.1.0
   - Flask-CORS==6.0.1
   - ReportLab==4.4.3 (pour la génération de PDF)
   - PyJWT==2.10.1
   - pytest==8.4.1 (pour les tests)
   - Autres dépendances (voir `requirements.txt` pour la liste complète)

## Configuration

L'application utilise les paramètres de configuration définis dans `config.py`. Vous pouvez surcharger les valeurs par défaut en définissant des variables d'environnement.

### Variables d'environnement

| Variable                   | Description                                                                        | Valeur par défaut       |
| -------------------------- | ---------------------------------------------------------------------------------- | ----------------------- |
| `FLASK_ENV`                | Mode d'environnement (`development` ou `production`)                               | `development`           |
| `SECRET_KEY`               | Clé secrète pour la signature JWT (obligatoire en production)                      | Générée aléatoirement   |
| `DATABASE_URL`             | URI de la base de données (ex. `postgresql://user:password@localhost:5432/pos_db`) | `sqlite:///database.db` |
| `ADMIN_PASSWORD`           | Mot de passe pour l'utilisateur admin par défaut (développement uniquement)        | `admin123`              |
| `TOKEN_EXPIRATION_MINUTES` | Durée d'expiration des tokens JWT en minutes                                       | `240`                   |
| `FRONTEND_URL`             | Origines autorisées pour CORS (séparées par des virgules)                          | `http://localhost:3000` |
| `PORT`                     | Port pour exécuter l'application                                                   | `8080`                  |

Exemple pour la production (Linux/Mac) :

```bash
export FLASK_ENV=production
export SECRET_KEY=clé-secrète-sécurisée
export DATABASE_URL=postgresql://utilisateur:motdepasse@localhost:5432/pos_db
export ADMIN_PASSWORD=mot-de-passe-admin-sécurisé
export FRONTEND_URL=http://votre-frontend.com
export PORT=5000
```

Sur Windows (PowerShell) :

```powershell
$env:FLASK_ENV="production"
$env:SECRET_KEY="clé-secrète-sécurisée"
$env:DATABASE_URL="postgresql://utilisateur:motdepasse@localhost:5432/pos_db"
$env:ADMIN_PASSWORD="mot-de-passe-admin-sécurisé"
$env:FRONTEND_URL="http://votre-frontend.com"   # par default : `http://localhost:3000`
$env:PORT="5000"
```

### Configuration de la base de données

- **SQLite** : Utilisé par défaut pour le développement. Aucun réglage supplémentaire requis.
- **PostgreSQL** (recommandé pour la production) :
  1. Installez PostgreSQL et créez une base de données (ex. `pos_db`).
  2. Définissez la variable d'environnement `DATABASE_URL`.
  3. Assurez-vous que l'utilisateur de la base de données a les permissions nécessaires.

## Exécution de l'application

1. **Appliquer les migrations** (crée les tables de la base de données et l'utilisateur admin par défaut) :

   ```bash
   python manage.py db upgrade
   ```

2. **Démarrer l'application** :

   ```bash
   python app.py
   ```

   L'application sera accessible sur `http://127.0.0.1:8080` (ou le port spécifié par `PORT`).

   En production, utilisez un serveur WSGI comme Gunicorn :

   ```bash
   gunicorn -w 4 -b 127.0.0.1:5000 app:app
   ```

## Gestion des migrations de base de données

L'application utilise Flask-Migrate pour gérer le schéma de la base de données. Pour gérer les migrations :

1. **Initialiser les migrations** (uniquement requis une fois) :

   ```bash
   python manage.py db init
   ```

2. **Générer des scripts de migration** après des modifications des modèles :

   ```bash
   python manage.py db migrate
   ```

3. **Appliquer les migrations** :
   ```bash
   python manage.py db upgrade
   ```

Pour annuler une migration :

```bash
python manage.py db downgrade
```

## Tests

Le fichier `test.py` inclut une suite de tests unitaires complète avec `unittest` pour valider le comportement de l'API. Les tests couvrent :

- Démarrage de l'application et connectivité à la base de données
- Authentification (connexion réussie, identifiants invalides, champs manquants)
- Gestion des utilisateurs (création, liste, restrictions de rôle)
- Gestion des catégories et des produits
- Création et récupération des ventes (JSON et PDF)
- Gestion des sessions de caisse
- Gestion des accès non autorisés et des tokens invalides

Exécuter les tests :

```bash
python -m unittest test.py -v
```

Pour les tests, l'application utilise une base de données SQLite en mémoire (`TestConfig`).

## Endpoints de l'API

Tous les endpoints sont préfixés par `/api`. L'authentification est requise pour tous les endpoints sauf `/api/login`. Voici un résumé des endpoints :

| Méthode | Endpoint                                         | Rôle     | Description                                      |
| ------- | ------------------------------------------------ | -------- | ------------------------------------------------ |
| POST    | `/login`                                         | Aucun    | Authentification et génération du token JWT      |
| POST    | `/users`                                         | Admin    | Créer un nouvel utilisateur                      |
| GET     | `/users`                                         | Admin    | Lister les utilisateurs actifs                   |
| POST    | `/categories`                                    | Admin    | Créer une nouvelle catégorie                     |
| PUT     | `/categories/<int:category_id>`                  | Admin    | Mettre à jour une catégorie                      |
| GET     | `/categories`                                    | Tous     | Lister les catégories actives                    |
| POST    | `/products`                                      | Admin    | Créer un nouveau produit                         |
| GET     | `/products`                                      | Tous     | Lister les produits actifs avec leurs catégories |
| POST    | `/sales`                                         | Caissier | Créer une nouvelle vente                         |
| GET     | `/sales`                                         | Tous     | Récupérer les ventes (JSON ou PDF, filtré)       |
| POST    | `/cash-register-sessions`                        | Caissier | Ouvrir une session de caisse                     |
| PUT     | `/cash-register-sessions/<int:session_id>/close` | Caissier | Fermer une session de caisse                     |

Pour une documentation détaillée des endpoints (paramètres, réponses, exemples), référez-vous au fichier `api_documentation.md`.

## Journalisation

Les journaux sont écrits dans `app.log` et sur la console avec le format suivant :

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

- **Niveaux** : INFO pour les opérations normales, ERROR pour les exceptions.
- **Exemples** :
  - `Login successful for user: admin`
  - `Error initializing database: <erreur>`
  - `Sale created: ID=1, Total=1000`

## Structure du projet

```
pos-api/
├── app.py              # Point d'entrée et configuration de l'application
├── config.py           # Paramètres de configuration (développement et tests)
├── models.py           # Modèles SQLAlchemy (User, Category, Product, etc.)
├── routes.py           # Endpoints de l'API et logique métier
├── manage.py           # CLI pour les migrations de base de données
├── test.py             # Tests unitaires
├── requirements.txt    # Dépendances
├── migrations/         # Scripts de migration (créés par Flask-Migrate)
└── app.log             # Fichier de journalisation
```

## Variables d'environnement

Assurez-vous de définir les variables suivantes pour la production :

- `SECRET_KEY` : Une clé sécurisée et unique pour la signature JWT.
- `DATABASE_URL` : URI PostgreSQL pour la base de données de production.
- `ADMIN_PASSWORD` : Mot de passe sécurisé pour l'utilisateur admin par défaut.
- `FRONTEND_URL` : Origines autorisées pour le frontend (CORS).

Exemple de fichier `.env` :

```bash
FLASK_ENV=production
SECRET_KEY=clé-secrète-sécurisée
DATABASE_URL=postgresql://utilisateur:motdepasse@localhost:5432/pos_db
ADMIN_PASSWORD=mot-de-passe-admin-sécurisé
FRONTEND_URL=http://votre-frontend.com
PORT=5000
TOKEN_EXPIRATION_MINUTES=240
```

Utilisez un outil comme `python-dotenv` pour charger le fichier `.env` en développement.

## Exemple d'utilisation

1. **Démarrer l'application** :

   ```bash
   python app.py
   ```

2. **Connexion en tant qu'admin** :

   ```bash
   curl -X POST http://127.0.0.1:8080/api/login -H "Content-Type: application/json" -d '{"username": "admin", "password": "admin123"}'
   ```

3. **Créer une catégorie** (avec le token admin) :

   ```bash
   curl -X POST http://127.0.0.1:8080/api/categories -H "Authorization: Bearer <token_admin>" -H "Content-Type: application/json" -d '{"name": "Électronique", "description": "Produits électroniques"}'
   ```

4. **Créer un produit** :

   ```bash
   curl -X POST http://127.0.0.1:8080/api/products -H "Authorization: Bearer <token_admin>" -H "Content-Type: application/json" -d '{"name": "Ordinateur portable", "price": 1000, "stock": 5, "category_id": 1, "description": "Ordinateur haut de gamme"}'
   ```

5. **Ouvrir une session de caisse** (en tant que caissier) :

   ```bash
   curl -X POST http://127.0.0.1:8080/api/cash-register-sessions -H "Authorization: Bearer <token_caissier>" -H "Content-Type: application/json" -d '{"starting_cash": 500}'
   ```

6. **Créer une vente** :

   ```bash
   curl -X POST http://127.0.0.1:8080/api/sales -H "Authorization: Bearer <token_caissier>" -H "Content-Type: application/json" -d '{"items": [{"product_id": 1, "quantity": 2}], "payment_method": "CASH"}'
   ```

7. **Récupérer un rapport de ventes (PDF)** :
   ```bash
   curl -X GET "http://127.0.0.1:8080/api/sales?format=pdf" -H "Authorization: Bearer <token_admin>" --output rapport_ventes.pdf
   ```
