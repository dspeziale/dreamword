# models.py
"""
Modelli di dati per l'applicazione
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from framework import DatabaseManager
from framework.exceptions import DuplicateKeyError, DatabaseError


@dataclass
class User:
    """Modello per gli utenti"""
    name: str
    email: str
    age: Optional[int] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte il modello in dizionario per database"""
        data = asdict(self)
        # Rimuovi campi None e id se auto-increment
        return {k: v for k, v in data.items() if v is not None and k != 'id'}


class UserRepository:
    """Repository per gestire le operazioni sui User"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_table(self):
        """Crea la tabella users se non esiste"""
        create_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.db.execute_raw(create_sql)

    def create(self, user: User) -> User:
        """Crea un nuovo utente"""
        try:
            user_data = user.to_dict()
            user_id = self.db.insert('users', user_data)

            # Recupera l'utente creato
            created_user = self.find_by_id(user_id)
            return created_user

        except DuplicateKeyError as e:
            raise ValueError(f"Email già esistente: {user.email}")

    def find_by_id(self, user_id: int) -> Optional[User]:
        """Trova un utente per ID"""
        result = self.db.select_one(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        return self._dict_to_user(result) if result else None

    def find_by_email(self, email: str) -> Optional[User]:
        """Trova un utente per email"""
        result = self.db.select_one(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        )
        return self._dict_to_user(result) if result else None

    def find_all(self, limit: Optional[int] = None) -> List[User]:
        """Trova tutti gli utenti"""
        query = "SELECT * FROM users ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"

        results = self.db.select(query)
        return [self._dict_to_user(row) for row in results]

    def find_by_age_range(self, min_age: int, max_age: int) -> List[User]:
        """Trova utenti per fascia di età"""
        results = self.db.select(
            "SELECT * FROM users WHERE age BETWEEN ? AND ? ORDER BY age",
            (min_age, max_age)
        )
        return [self._dict_to_user(row) for row in results]

    def update(self, user_id: int, updates: Dict[str, Any]) -> Optional[User]:
        """Aggiorna un utente"""
        # Aggiungi timestamp di aggiornamento
        updates['updated_at'] = datetime.now().isoformat()

        affected = self.db.update(
            'users',
            updates,
            'id = ?',
            (user_id,)
        )

        return self.find_by_id(user_id) if affected > 0 else None

    def delete(self, user_id: int) -> bool:
        """Elimina un utente"""
        affected = self.db.delete('users', 'id = ?', (user_id,))
        return affected > 0

    def count(self) -> int:
        """Conta tutti gli utenti"""
        return self.db.count('users')

    def exists_email(self, email: str) -> bool:
        """Verifica se esiste un utente con questa email"""
        return self.db.exists('users', 'email = ?', (email,))

    def search_by_name(self, name_pattern: str) -> List[User]:
        """Cerca utenti per nome (pattern matching)"""
        results = self.db.select(
            "SELECT * FROM users WHERE name LIKE ? ORDER BY name",
            (f"%{name_pattern}%",)
        )
        return [self._dict_to_user(row) for row in results]

    def _dict_to_user(self, data: Dict[str, Any]) -> User:
        """Converte un dizionario in User"""
        return User(
            id=data.get('id'),
            name=data['name'],
            email=data['email'],
            age=data.get('age'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None
        )


@dataclass
class Product:
    """Modello per i prodotti"""
    name: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None and k != 'id'}


class ProductRepository:
    """Repository per gestire le operazioni sui Product"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def create_table(self):
        """Crea la tabella products se non esiste"""
        create_sql = """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                description TEXT,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self.db.execute_raw(create_sql)

    def create(self, product: Product) -> Product:
        """Crea un nuovo prodotto"""
        product_data = product.to_dict()
        product_id = self.db.insert('products', product_data)
        return self.find_by_id(product_id)

    def find_by_id(self, product_id: int) -> Optional[Product]:
        """Trova un prodotto per ID"""
        result = self.db.select_one(
            "SELECT * FROM products WHERE id = ?",
            (product_id,)
        )
        return self._dict_to_product(result) if result else None

    def find_by_category(self, category: str) -> List[Product]:
        """Trova prodotti per categoria"""
        results = self.db.select(
            "SELECT * FROM products WHERE category = ? ORDER BY name",
            (category,)
        )
        return [self._dict_to_product(row) for row in results]

    def find_by_price_range(self, min_price: float, max_price: float) -> List[Product]:
        """Trova prodotti per fascia di prezzo"""
        results = self.db.select(
            "SELECT * FROM products WHERE price BETWEEN ? AND ? ORDER BY price",
            (min_price, max_price)
        )
        return [self._dict_to_product(row) for row in results]

    def find_all(self, limit: Optional[int] = None) -> List[Product]:
        """Trova tutti i prodotti"""
        query = "SELECT * FROM products ORDER BY created_at DESC"
        if limit:
            query += f" LIMIT {limit}"

        results = self.db.select(query)
        return [self._dict_to_product(row) for row in results]

    def update(self, product_id: int, updates: Dict[str, Any]) -> Optional[Product]:
        """Aggiorna un prodotto"""
        affected = self.db.update(
            'products',
            updates,
            'id = ?',
            (product_id,)
        )

        return self.find_by_id(product_id) if affected > 0 else None

    def delete(self, product_id: int) -> bool:
        """Elimina un prodotto"""
        affected = self.db.delete('products', 'id = ?', (product_id,))
        return affected > 0

    def count(self) -> int:
        """Conta tutti i prodotti"""
        return self.db.count('products')

    def _dict_to_product(self, data: Dict[str, Any]) -> Product:
        """Converte un dizionario in Product"""
        return Product(
            id=data.get('id'),
            name=data['name'],
            price=data['price'],
            description=data.get('description'),
            category=data.get('category'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None
        )