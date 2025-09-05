# Documentation de l'API Point de Vente

Cette documentation fournit une description complète et détaillée de chaque endpoint de l'API définie dans le fichier `routes.py`. L'API est implémentée avec **Flask** et utilise un **Blueprint** nommé `api` avec le préfixe URL `/api`. Tous les endpoints, sauf `/api/login`, nécessitent une authentification via un token **JWT** fourni dans l'en-tête `Authorization: Bearer <token>`. Les rôles (`ADMIN` ou `CASHIER`) sont strictement vérifiés, et des erreurs spécifiques sont renvoyées pour les violations d'autorisation.

Les réponses sont généralement au format **JSON**, sauf pour l'endpoint `/api/sales` qui peut retourner un fichier **PDF** si le paramètre `format=pdf` est spécifié. Les erreurs sont renvoyées avec un code HTTP approprié et un message JSON de la forme `{ "error": "message" }`. Les modèles de données incluent : `User`, `Category`, `Product`, `Sale`, `SaleItem`, `CashRegisterSession`, `Role` (enum: `ADMIN`, `CASHIER`), et `PaymentMethod` (enum: `CASH`, `CARD`, etc.).

## Table des Matières

- [Authentification](#authentification)
- [Modèles de Données](#modèles-de-données)
- [Endpoints](#endpoints)
  - [1. POST /api/login](#1-post-apilogin)
  - [2. POST /api/users](#2-post-apiusers)
  - [3. GET /api/users](#3-get-apiusers)
  - [4. POST /api/categories](#4-post-apicategories)
  - [5. PUT /api/categories/<int:category_id>](#5-put-apicategoriesintcategory_id)
  - [6. GET /api/categories](#6-get-apicategories)
  - [7. POST /api/products](#7-post-apiproducts)
  - [8. GET /api/products](#8-get-apiproducts)
  - [9. POST /api/sales](#9-post-apisales)
  - [10. GET /api/sales](#10-get-apisales)
  - [11. POST /api/cash-register-sessions](#11-post-apicash-register-sessions)
  - [12. PUT /api/cash-register-sessions/<int:session_id>/close](#12-put-apicash-register-sessionsintsession_idclose)
- [Notes Techniques](#notes-techniques)
- [Tests](#tests)
- [Exemple d'Utilisation](#exemple-dutilisation)

## Authentification

- **Mécanisme** : Les endpoints protégés utilisent le décorateur `_require_auth` pour valider un token JWT signé avec `SECRET_KEY` (algorithme HS256). Le token inclut `user_id`, `role`, et une date d'expiration (`exp`).
- **Expiration** : Les tokens expirent après `TOKEN_EXPIRATION_MINUTES` minutes (défini dans `Config`).
- **Rôles** :
  - `ADMIN` : Accès à la gestion des utilisateurs, catégories, et produits.
  - `CASHIER` : Accès aux ventes et sessions de caisse.
- **Vérifications** :
  - L'utilisateur doit être actif (`is_active=True`).
  - Le rôle est vérifié si spécifié dans `_require_auth(required_role)`.
  - Erreurs possibles : token manquant, invalide (`jwt.InvalidTokenError`), expiré (`jwt.ExpiredSignatureError`), utilisateur inactif, ou rôle incorrect.

## Modèles de Données

Les modèles sont définis dans `models.py` et utilisent **SQLAlchemy** pour interagir avec la base de données. Voici un résumé des modèles principaux :

- **User** :

  - `id` (int) : Clé primaire.
  - `username` (string) : Unique, 3-50 caractères alphanumériques ou underscores.
  - `password_hash` (string) : Mot de passe hashé.
  - `role` (enum Role) : `ADMIN` ou `CASHIER`.
  - `is_active` (boolean) : Statut actif (par défaut `True`).
  - `created_at`, `updated_at` (datetime) : Horodatages.
  - Méthode : `to_dict()` pour sérialisation JSON.

- **Category** :

  - `id` (int) : Clé primaire.
  - `name` (string) : Unique.
  - `description` (string) : Optionnel.
  - `is_active` (boolean) : Statut actif.
  - `created_at`, `updated_at` (datetime).
  - Méthode : `to_dict()`.

- **Product** :

  - `id` (int) : Clé primaire.
  - `name` (string) : Unique.
  - `price` (int) : Prix en unité monétaire (entier).
  - `stock` (int) : Quantité en stock (non négatif).
  - `category_id` (int) : Clé étrangère vers `Category`.
  - `description` (string) : Optionnel.
  - `is_active` (boolean).
  - `created_at`, `updated_at` (datetime).
  - Relation : `category` (via SQLAlchemy).
  - Méthode : `to_dict()`.

- **Sale** :

  - `id` (int) : Clé primaire.
  - `total` (int) : Total calculé (somme des `quantity * unit_price` des `SaleItem`).
  - `payment_method` (enum PaymentMethod) : `CASH`, `CARD`, etc.
  - `user_id` (int) : Clé étrangère vers `User`.
  - `session_id` (int) : Clé étrangère vers `CashRegisterSession`.
  - `date` (datetime) : Date de la vente.
  - `is_active` (boolean).
  - Relation : `items` (liste de `SaleItem`), `user` (via SQLAlchemy).
  - Méthode : `to_dict()`.

- **SaleItem** :

  - `id` (int) : Clé primaire.
  - `sale_id` (int) : Clé étrangère vers `Sale`.
  - `product_id` (int) : Clé étrangère vers `Product`.
  - `quantity` (int) : Quantité vendue (positif).
  - `unit_price` (int) : Prix unitaire au moment de la vente.
  - Relation : `product` (via SQLAlchemy).
  - Méthode : `to_dict()`.

- **CashRegisterSession** :
  - `id` (int) : Clé primaire.
  - `user_id` (int) : Clé étrangère vers `User`.
  - `starting_cash` (int) : Montant initial (non négatif).
  - `ending_cash` (int) : Montant final (null jusqu'à fermeture).
  - `status` (string) : `open` ou `closed`.
  - `start_time`, `end_time` (datetime) : Horodatages.
  - Méthode : `to_dict()`.

## Endpoints

### 1. POST /api/login

**Description** : Authentifie un utilisateur et génère un token JWT. Aucun token préalable n'est requis. Vérifie les identifiants et l'état actif de l'utilisateur.

**Méthode** : POST  
**URL** : `/api/login`  
**Paramètres** :

- **Body (JSON, requis)** :
  - `username` (string) : Nom d'utilisateur.
  - `password` (string) : Mot de passe brut.

**Headers** : Aucun.

**Réponses** :

- **200 OK** : Authentification réussie.
  ```json
  {
    "message": "Welcome <username>",
    "token": "<jwt_token>",
    "user": {
      "id": <int>,
      "username": "<string>",
      "role": "<ADMIN|CASHIER>",
      "is_active": true,
      "created_at": "<ISO datetime>",
      "updated_at": "<ISO datetime>"
    }
  }
  ```
- **400 Bad Request** : `{ "error": "Username and password required" }` si les champs sont absents.
- **401 Unauthorized** :
  - `{ "error": "Invalid credentials" }` : Identifiants incorrects.
  - `{ "error": "Account is inactive" }` : Utilisateur inactif.

**Exemple de requête** :

```json
{
  "username": "admin",
  "password": "adminpass"
}
```

**Exemple de réponse (200)** :

```json
{
  "message": "Welcome admin",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "ADMIN",
    "is_active": true,
    "created_at": "2025-09-05T11:43:00Z",
    "updated_at": "2025-09-05T11:43:00Z"
  }
}
```

**Logs** :

- Succès : `Login successful for user: <username>`.
- Erreurs : Identifiants manquants, invalides, ou utilisateur inactif.

### 2. POST /api/users

**Description** : Crée un nouvel utilisateur. Réservé aux admins. Le nom d'utilisateur doit être unique et respecter le format regex `^[a-zA-Z0-9_]{3,50}$`. Le mot de passe est hashé avec `generate_password_hash`.

**Méthode** : POST  
**URL** : `/api/users`  
**Paramètres** :

- **Body (JSON, requis)** :
  - `username` (string) : 3-50 caractères alphanumériques ou underscores.
  - `password` (string) : Mot de passe brut.
  - `role` (string) : "ADMIN" ou "CASHIER".

**Headers** :

- `Authorization: Bearer <admin_token>` (rôle ADMIN requis).

**Réponses** :

- **201 Created** : Utilisateur créé.
  ```json
  {
    "id": <int>,
    "username": "<string>",
    "role": "<ADMIN|CASHIER>",
    "is_active": true,
    "created_at": "<ISO datetime>",
    "updated_at": "<ISO datetime>"
  }
  ```
- **400 Bad Request** :
  - `{ "error": "Username, password, and role required" }` : Champs manquants.
  - `{ "error": "Username must be 3-50 alphanumeric characters or underscores" }` : Format invalide.
  - `{ "error": "Invalid role" }` : Rôle non reconnu.
  - `{ "error": "Username already exists" }` : Duplicata.
- **401 Unauthorized** :
  - `{ "error": "Authorization token required" }` : Token manquant.
  - `{ "error": "Token expired" }` : Token expiré.
  - `{ "error": "Invalid token" }` : Token invalide.
  - `{ "error": "Authentication failed" }` : Erreur générale.
- **403 Forbidden** : `{ "error": "ADMIN role required" }` : Rôle incorrect.

**Exemple de requête** :

```json
{
  "username": "newcashier",
  "password": "securepass",
  "role": "CASHIER"
}
```

**Logs** :

- Succès : `User created: <username>`.
- Erreurs : Champs manquants, format username invalide, rôle invalide, ou duplicata.

### 3. GET /api/users

**Description** : Récupère la liste des utilisateurs actifs. Réservé aux admins.

**Méthode** : GET  
**URL** : `/api/users`  
**Paramètres** : Aucun.

**Headers** :

- `Authorization: Bearer <admin_token>` (rôle ADMIN requis).

**Réponses** :

- **200 OK** : Liste des utilisateurs.
  ```json
  [
    {
      "id": <int>,
      "username": "<string>",
      "role": "<ADMIN|CASHIER>",
      "is_active": true,
      "created_at": "<ISO datetime>",
      "updated_at": "<ISO datetime>"
    },
    ...
  ]
  ```
- **401 Unauthorized** : Token manquant, invalide, expiré, ou utilisateur inactif.
- **403 Forbidden** : Rôle non admin.

**Logs** :

- Succès : `Processing get users request`.

### 4. POST /api/categories

**Description** : Crée une nouvelle catégorie. Réservé aux admins. Le nom doit être unique.

**Méthode** : POST  
**URL** : `/api/categories`  
**Paramètres** :

- **Body (JSON, requis)** :
  - `name` (string) : Nom unique de la catégorie.
  - `description` (string, optionnel) : Description.

**Headers** :

- `Authorization: Bearer <admin_token>` (rôle ADMIN requis).

**Réponses** :

- **201 Created** : Catégorie créée.
  ```json
  {
    "id": <int>,
    "name": "<string>",
    "description": "<string>",
    "is_active": true,
    "created_at": "<ISO datetime>",
    "updated_at": "<ISO datetime>"
  }
  ```
- **400 Bad Request** :
  - `{ "error": "Name required" }` : Champ manquant.
  - `{ "error": "Category name already exists" }` : Duplicata.
- **401 Unauthorized** : Token manquant, invalide, ou expiré.
- **403 Forbidden** : Rôle non admin.

**Exemple de requête** :

```json
{
  "name": "Électronique",
  "description": "Produits électroniques"
}
```

**Logs** :

- Succès : `Category created: <name>`.
- Erreurs : Champ manquant ou duplicata.

### 5. PUT /api/categories/<int:category_id>

**Description** : Met à jour une catégorie existante. Réservé aux admins. Le nom doit rester unique. La date `updated_at` est mise à jour.

**Méthode** : PUT  
**URL** : `/api/categories/<category_id>`  
**Paramètres** :

- **Path** :
  - `category_id` (int) : ID de la catégorie.
- **Body (JSON, requis)** :
  - `name` (string) : Nouveau nom.
  - `description` (string, optionnel) : Nouvelle description (par défaut, conserve l'existante).

**Headers** :

- `Authorization: Bearer <admin_token>` (rôle ADMIN requis).

**Réponses** :

- **200 OK** : Catégorie mise à jour.
  ```json
  {
    "id": <int>,
    "name": "<string>",
    "description": "<string>",
    "is_active": true,
    "created_at": "<ISO datetime>",
    "updated_at": "<ISO datetime>"
  }
  ```
- **400 Bad Request** :
  - `{ "error": "Name required" }` : Champ manquant.
  - `{ "error": "Category name already exists" }` : Duplicata.
- **404 Not Found** : `{ "error": "Category not found" }`.
- **401 Unauthorized** : Token manquant, invalide, ou expiré.
- **403 Forbidden** : Rôle non admin.

**Exemple de requête** :

```json
{
  "name": "Électronique Mise à Jour",
  "description": "Nouvelle description"
}
```

**Logs** :

- Succès : `Category updated: <name>`.
- Erreurs : Catégorie non trouvée, champ manquant, ou duplicata.

### 6. GET /api/categories

**Description** : Récupère la liste des catégories actives. Accessible à tous les utilisateurs authentifiés.

**Méthode** : GET  
**URL** : `/api/categories`  
**Paramètres** : Aucun.

**Headers** :

- `Authorization: Bearer <token>` (requis, tout rôle).

**Réponses** :

- **200 OK** : Liste des catégories.
  ```json
  [
    {
      "id": <int>,
      "name": "<string>",
      "description": "<string>",
      "is_active": true,
      "created_at": "<ISO datetime>",
      "updated_at": "<ISO datetime>"
    },
    ...
  ]
  ```
- **401 Unauthorized** : Token manquant, invalide, expiré, ou utilisateur inactif.

**Logs** :

- Succès : `Processing get categories request`.

### 7. POST /api/products

**Description** : Crée un nouveau produit. Réservé aux admins. Le prix doit être un entier positif, le stock non négatif, et le nom unique.

**Méthode** : POST  
**URL** : `/api/products`  
**Paramètres** :

- **Body (JSON, requis)** :
  - `name` (string) : Nom unique du produit.
  - `price` (int) : Prix (entier positif).
  - `stock` (int) : Stock initial (non négatif).
  - `category_id` (int) : ID de la catégorie.
  - `description` (string, optionnel) : Description.

**Headers** :

- `Authorization: Bearer <admin_token>` (rôle ADMIN requis).

**Réponses** :

- **201 Created** : Produit créé.
  ```json
  {
    "id": <int>,
    "name": "<string>",
    "price": <int>,
    "stock": <int>,
    "category_id": <int>,
    "description": "<string>",
    "is_active": true,
    "created_at": "<ISO datetime>",
    "updated_at": "<ISO datetime>"
  }
  ```
- **400 Bad Request** :
  - `{ "error": "Name, price, stock, and category_id required" }` : Champs manquants.
  - `{ "error": "Price must be an integer" }` : Type incorrect.
  - `{ "error": "Stock cannot be negative" }` : Stock invalide.
  - `{ "error": "Product name already exists" }` : Duplicata.
- **401 Unauthorized** : Token manquant, invalide, ou expiré.
- **403 Forbidden** : Rôle non admin.

**Exemple de requête** :

```json
{
  "name": "Ordinateur",
  "price": 1000,
  "stock": 5,
  "category_id": 1,
  "description": "Ordinateur portable"
}
```

**Logs** :

- Succès : `Product created: <name>`.
- Erreurs : Champs manquants, type de prix invalide, stock négatif, ou duplicata.

### 8. GET /api/products

**Description** : Récupère la liste des produits actifs avec leurs catégories (via `selectinload`). Accessible à tous les utilisateurs authentifiés.

**Méthode** : GET  
**URL** : `/api/products`  
**Paramètres** : Aucun.

**Headers** :

- `Authorization: Bearer <token>` (requis, tout rôle).

**Réponses** :

- **200 OK** : Liste des produits.
  ```json
  [
    {
      "id": <int>,
      "name": "<string>",
      "price": <int>,
      "stock": <int>,
      "category_id": <int>,
      "category": {
        "id": <int>,
        "name": "<string>",
        "description": "<string>",
        "is_active": true,
        "created_at": "<ISO datetime>",
        "updated_at": "<ISO datetime>"
      },
      "description": "<string>",
      "is_active": true,
      "created_at": "<ISO datetime>",
      "updated_at": "<ISO datetime>"
    },
    ...
  ]
  ```
- **401 Unauthorized** : Token manquant, invalide, expiré, ou utilisateur inactif.

**Logs** :

- Succès : `Processing get products request`.

### 9. POST /api/sales

**Description** : Crée une nouvelle vente. Réservé aux caissiers. Nécessite une session de caisse ouverte (`status="open"`). Met à jour le stock des produits. Le total est calculé automatiquement (somme des `quantity * unit_price`).

**Méthode** : POST  
**URL** : `/api/sales`  
**Paramètres** :

- **Body (JSON, requis)** :
  - `items` (array) : Liste d'objets `{ "product_id": <int>, "quantity": <int> (positif) }`.
  - `payment_method` (string) : "CASH" ou "CARD" (enum `PaymentMethod`).

**Headers** :

- `Authorization: Bearer <cashier_token>` (rôle CASHIER requis).

**Réponses** :

- **201 Created** : Vente créée.
  ```json
  {
    "id": <int>,
    "total": <int>,
    "payment_method": "<CASH|CARD>",
    "date": "<ISO datetime>",
    "user_id": <int>,
    "session_id": <int>,
    "items": [
      {
        "id": <int>,
        "product_id": <int>,
        "quantity": <int>,
        "unit_price": <int>
      },
      ...
    ]
  }
  ```
- **400 Bad Request** :
  - `{ "error": "Items and payment_method required" }` : Champs manquants.
  - `{ "error": "Invalid payment method" }` : Méthode non reconnue.
  - `{ "error": "No open cash register session" }` : Pas de session ouverte.
  - `{ "error": "Quantity must be positive" }` : Quantité invalide.
  - `{ "error": "Insufficient stock for <product_name>" }` : Stock insuffisant.
  - `{ "error": "Failed to create sale" }` : Erreur générale.
- **404 Not Found** : `{ "error": "Product ID <id> not found" }`.
- **401 Unauthorized** : Token manquant, invalide, ou expiré.
- **403 Forbidden** : Rôle non cashier.

**Exemple de requête** :

```json
{
  "items": [{ "product_id": 1, "quantity": 2 }],
  "payment_method": "CASH"
}
```

**Logs** :

- Succès : `Sale created: ID=<id>, Total=<total>`.
- Erreurs : Champs manquants, méthode de paiement invalide, pas de session, produit non trouvé, quantité invalide, ou stock insuffisant.

### 10. GET /api/sales

**Description** : Récupère les ventes avec filtres optionnels. Les non-admins ne peuvent voir que leurs propres ventes. Supporte l'exportation en PDF avec `ReportLab`.

**Méthode** : GET  
**URL** : `/api/sales`  
**Paramètres (Query, optionnels)** :

- `start_date` (string) : Date de début (ISO, ex: "2025-09-01T00:00:00Z").
- `end_date` (string) : Date de fin (ISO).
- `user_id` (int) : Filtrer par utilisateur (admins uniquement pour autres users).
- `category_id` (int) : Filtrer par catégorie des produits.
- `product_id` (int) : Filtrer par produit.
- `format` (string) : "json" (défaut) ou "pdf".

**Headers** :

- `Authorization: Bearer <token>` (requis, tout rôle).

**Réponses** :

- **200 OK (JSON)** :
  ```json
  {
    "sales": [
      {
        "id": <int>,
        "total": <int>,
        "payment_method": "<CASH|CARD>",
        "date": "<ISO datetime>",
        "user_id": <int>,
        "session_id": <int>,
        "items": [
          {
            "id": <int>,
            "product_id": <int>,
            "quantity": <int>,
            "unit_price": <int>,
            "product_name": "<string>"
          },
          ...
        ],
        "user_name": "<string>"
      },
      ...
    ],
    "total": <int>
  }
  ```
- **200 OK (PDF)** : Fichier `sales_report.pdf` avec tableau (colonnes : ID, Date, User, Total, Items) et total global.
- **400 Bad Request** :
  - `{ "error": "User ID must be an integer" }` : `user_id` non entier.
  - `{ "error": "Category ID must be an integer" }` : `category_id` non entier.
  - `{ "error": "Product ID must be an integer" }` : `product_id` non entier.
  - `{ "error": "Invalid date format (use ISO format)" }` : Date invalide.
- **403 Forbidden** : `{ "error": "Cannot access other users’ data" }` : Non-admin accédant à d'autres utilisateurs.
- **404 Not Found** : `{ "error": "Category not found" }`.
- **401 Unauthorized** : Token manquant, invalide, ou expiré.

**Logs** :

- Succès : `Retrieved <count> sales` ou `Generated PDF sales report`.
- Erreurs : Filtres invalides, accès non autorisé, ou catégorie non trouvée.

### 11. POST /api/cash-register-sessions

**Description** : Ouvre une nouvelle session de caisse. Réservé aux caissiers. Un utilisateur ne peut avoir qu'une seule session ouverte à la fois.

**Méthode** : POST  
**URL** : `/api/cash-register-sessions`  
**Paramètres** :

- **Body (JSON, requis)** :
  - `starting_cash` (int) : Montant initial (non négatif).

**Headers** :

- `Authorization: Bearer <cashier_token>` (rôle CASHIER requis).

**Réponses** :

- **201 Created** : Session ouverte.
  ```json
  {
    "id": <int>,
    "user_id": <int>,
    "starting_cash": <int>,
    "ending_cash": null,
    "status": "open",
    "start_time": "<ISO datetime>",
    "end_time": null
  }
  ```
- **400 Bad Request** :
  - `{ "error": "Starting cash required" }` : Champ manquant.
  - `{ "error": "Starting cash must be a non-negative integer" }` : Valeur invalide.
  - `{ "error": "User already has an open session" }` : Session existante.
- **401 Unauthorized** : Token manquant, invalide, ou expiré.
- **403 Forbidden** : Rôle non cashier.

**Exemple de requête** :

```json
{
  "starting_cash": 500
}
```

**Logs** :

- Succès : `Cash register session opened: ID=<id>`.
- Erreurs : Champ manquant, valeur invalide, ou session existante.

### 12. PUT /api/cash-register-sessions/<int:session_id>/close

**Description** : Ferme une session de caisse ouverte. Réservé au caissier propriétaire. Met à jour `ending_cash`, `status` ("closed"), et `end_time`.

**Méthode** : PUT  
**URL** : `/api/cash-register-sessions/<session_id>/close`  
**Paramètres** :

- **Path** :
  - `session_id` (int) : ID de la session.
- **Body (JSON, requis)** :
  - `ending_cash` (int) : Montant final (non négatif).

**Headers** :

- `Authorization: Bearer <cashier_token>` (rôle CASHIER requis).

**Réponses** :

- **200 OK** : Session fermée.
  ```json
  {
    "id": <int>,
    "user_id": <int>,
    "starting_cash": <int>,
    "ending_cash": <int>,
    "status": "closed",
    "start_time": "<ISO datetime>",
    "end_time": "<ISO datetime>"
  }
  ```
- **400 Bad Request** :
  - `{ "error": "Ending cash required" }` : Champ manquant.
  - `{ "error": "Ending cash must be a non-negative integer" }` : Valeur invalide.
  - `{ "error": "Session already closed" }` : Session déjà fermée.
- **404 Not Found** : `{ "error": "Session not found" }`.
- **403 Forbidden** : `{ "error": "Not authorized to close this session" }` : Non propriétaire ou rôle incorrect.
- **401 Unauthorized** : Token manquant, invalide, ou expiré.

**Exemple de requête** :

```json
{
  "ending_cash": 1000
}
```

**Logs** :

- Succès : `Cash register session closed: ID=<id>`.
- Erreurs : Session non trouvée, non autorisée, champ manquant, ou déjà fermée.

## Notes Techniques

- **Gestion des erreurs** :
  - Les exceptions SQLAlchemy (`IntegrityError` pour duplicatas) sont capturées et renvoient des messages spécifiques.
  - Les erreurs JWT (expiration, invalidité) sont gérées par le décorateur `_require_auth`.
  - Les logs sont enregistrés avec `logging.getLogger(__name__)` pour le débogage.
- **Sécurité** :
  - Tokens JWT signés avec `SECRET_KEY` (HS256).
  - Vérification stricte des rôles et de l'état actif des utilisateurs.
  - Protection contre les accès non autorisés (ex: non-admins accédant à d'autres utilisateurs).
- **Génération PDF** :
  - Utilise `ReportLab` pour créer des rapports tabulaires (utilisé dans `/api/sales?format=pdf`).
  - Format A4, tableau stylisé avec en-tête gris et corps beige, grille noire.
- **Base de données** :
  - Utilise SQLAlchemy avec chargement optimisé (`selectinload` pour les relations comme `Product.category`).
  - Transactions protégées avec rollback en cas d'erreur (ex: `db.session.rollback()`).
- **Configuration** :
  - `SECRET_KEY` et `TOKEN_EXPIRATION_MINUTES` sont définis dans `Config`.
  - Les endpoints sont enregistrés via `app.register_blueprint(api, url_prefix='/api')`.

## Tests

Le fichier `test.py` fournit une suite de tests complète avec **unittest** pour valider le comportement de l'API. Les cas incluent :

- **Configuration** : Vérification que l'application démarre et que la base de données est accessible.
- **Authentification** : Tests de connexion réussie, échec (mauvais mot de passe, champs manquants), et token invalide.
- **Utilisateurs** : Création par admin, échec pour caissier, username invalide, modèle `User`.
- **Catégories** : Création, mise à jour, récupération.
- **Produits** : Création, récupération, validation du type de prix (doit être entier).
- **Ventes** : Création, récupération, validation du stock et de la session de caisse.
- **Sessions de caisse** : Ouverture, fermeture, validation des montants.
- **Accès non autorisé** : Tests pour token manquant ou rôle incorrect.

**Exemple de test** (tiré de `test.py`) :

```python
def test_create_user_as_admin(self):
    headers = {"Authorization": f"Bearer {self.admin_token}"}
    user_data = {
        "username": "newuser",
        "password": "newpass",
        "role": "cashier"
    }
    response = self.client.post("/api/users", json=user_data, headers=headers)
    self.assertEqual(response.status_code, 201)
```

## Exemple d'Utilisation

Voici un scénario typique d'utilisation de l'API :

1. **Connexion** : Un caissier se connecte pour obtenir un token.

   ```bash
   curl -X POST http://localhost:5000/api/login -H "Content-Type: application/json" -d '{"username": "cashier", "password": "cashierpass"}'
   ```

2. **Ouverture de session de caisse** : Le caissier ouvre une session.

   ```bash
   curl -X POST http://localhost:5000/api/cash-register-sessions -H "Authorization: Bearer <cashier_token>" -H "Content-Type: application/json" -d '{"starting_cash": 500}'
   ```

3. **Création d'une vente** : Le caissier enregistre une vente.

   ```bash
   curl -X POST http://localhost:5000/api/sales -H "Authorization: Bearer <cashier_token>" -H "Content-Type: application/json" -d '{"items": [{"product_id": 1, "quantity": 2}], "payment_method": "CASH"}'
   ```

4. **Récupération des ventes (admin)** : Un admin récupère un rapport PDF.

   ```bash
   curl -X GET "http://localhost:5000/api/sales?format=pdf" -H "Authorization: Bearer <admin_token>" --output sales_report.pdf
   ```

5. **Fermeture de session** : Le caissier ferme sa session.
   ```bash
   curl -X PUT http://localhost:5000/api/cash-register-sessions/1/close -H "Authorization: Bearer <cashier_token>" -H "Content-Type: application/json" -d '{"ending_cash": 1000}'
   ```

Cette documentation est basée sur une analyse approfondie du code fourni dans `routes.py` et `test.py`. Elle couvre tous les aspects de l'API, y compris les entrées, sorties, erreurs, et logs. Pour toute modification ou extension de l'API, veuillez mettre à jour cette documentation en conséquence.
