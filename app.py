# app.py
"""
Applicazione principale - Dimostra l'uso del Database Framework
"""

import logging
from typing import List
from datetime import datetime

from framework import DatabaseManager
from framework.exceptions import DuplicateKeyError, DatabaseError
from config import DATABASE_CONFIG, APP_NAME, VERSION, LOG_LEVEL
from models import User, Product, UserRepository, ProductRepository

# Configurazione logging
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Application:
    """Classe principale dell'applicazione"""

    def __init__(self):
        self.db_manager = None
        self.user_repo = None
        self.product_repo = None

    def initialize(self):
        """Inizializza l'applicazione"""
        logger.info(f"Inizializzando {APP_NAME} v{VERSION}")
        logger.info(f"Database: {DATABASE_CONFIG.db_type.value}")

        # Crea connessione database
        self.db_manager = DatabaseManager(DATABASE_CONFIG)

        # Inizializza repository
        self.user_repo = UserRepository(self.db_manager)
        self.product_repo = ProductRepository(self.db_manager)

    def setup_database(self):
        """Crea le tabelle del database"""
        logger.info("Creando tabelle database...")

        with self.db_manager as db:
            self.user_repo.create_table()
            self.product_repo.create_table()

        logger.info("Database configurato correttamente")

    def demo_users(self):
        """Dimostra le operazioni sugli utenti"""
        print("\n" + "=" * 50)
        print("🧑‍💼 DEMO GESTIONE UTENTI")
        print("=" * 50)

        with self.db_manager as db:
            try:
                # Crea utenti di esempio
                users_data = [
                    User("Mario Rossi", "mario@example.com", 30),
                    User("Luigi Verdi", "luigi@example.com", 25),
                    User("Anna Bianchi", "anna@example.com", 35),
                    User("Paolo Neri", "paolo@example.com", 28)
                ]

                print("➕ Creando utenti...")
                created_users = []
                for user_data in users_data:
                    try:
                        user = self.user_repo.create(user_data)
                        created_users.append(user)
                        print(f"   ✅ {user.name} (ID: {user.id})")
                    except ValueError as e:
                        print(f"   ❌ Errore: {e}")

                # Mostra tutti gli utenti
                print(f"\n📋 Lista utenti (totale: {self.user_repo.count()}):")
                all_users = self.user_repo.find_all()
                for user in all_users:
                    print(f"   • {user.name} ({user.email}) - {user.age} anni")

                # Ricerca per email
                print(f"\n🔍 Ricerca per email 'mario@example.com':")
                found_user = self.user_repo.find_by_email("mario@example.com")
                if found_user:
                    print(f"   Trovato: {found_user.name} (ID: {found_user.id})")

                # Ricerca per fascia di età
                print(f"\n🔍 Utenti tra 25 e 30 anni:")
                young_users = self.user_repo.find_by_age_range(25, 30)
                for user in young_users:
                    print(f"   • {user.name} - {user.age} anni")

                # Aggiornamento
                if created_users:
                    user_to_update = created_users[0]
                    print(f"\n✏️  Aggiornando {user_to_update.name}...")
                    updated_user = self.user_repo.update(user_to_update.id, {
                        'age': 31,
                        'name': 'Mario Rossi Senior'
                    })
                    if updated_user:
                        print(f"   ✅ Aggiornato: {updated_user.name} - {updated_user.age} anni")

                # Ricerca per nome
                print(f"\n🔍 Ricerca per nome 'Mario':")
                mario_users = self.user_repo.search_by_name("Mario")
                for user in mario_users:
                    print(f"   • {user.name} ({user.email})")

                # Test duplicati
                print(f"\n⚠️  Test gestione duplicati...")
                try:
                    duplicate_user = User("Test Duplicate", "mario@example.com", 40)
                    self.user_repo.create(duplicate_user)
                except ValueError as e:
                    print(f"   ✅ Errore gestito correttamente: {e}")

            except Exception as e:
                logger.error(f"Errore demo utenti: {e}")
                print(f"❌ Errore: {e}")

    def demo_products(self):
        """Dimostra le operazioni sui prodotti"""
        print("\n" + "=" * 50)
        print("🛒 DEMO GESTIONE PRODOTTI")
        print("=" * 50)

        with self.db_manager as db:
            try:
                # Crea prodotti di esempio
                products_data = [
                    Product("Laptop", 999.99, "Computer portatile", "Elettronica"),
                    Product("Mouse", 29.99, "Mouse wireless", "Elettronica"),
                    Product("Scrivania", 199.50, "Scrivania in legno", "Arredamento"),
                    Product("Sedia", 149.99, "Sedia da ufficio", "Arredamento"),
                    Product("Smartphone", 699.00, "Telefono intelligente", "Elettronica")
                ]

                print("➕ Creando prodotti...")
                for product_data in products_data:
                    product = self.product_repo.create(product_data)
                    print(f"   ✅ {product.name} - €{product.price}")

                # Mostra tutti i prodotti
                print(f"\n📋 Lista prodotti (totale: {self.product_repo.count()}):")
                all_products = self.product_repo.find_all()
                for product in all_products:
                    print(f"   • {product.name} - €{product.price} ({product.category})")

                # Ricerca per categoria
                print(f"\n🔍 Prodotti categoria 'Elettronica':")
                electronics = self.product_repo.find_by_category("Elettronica")
                for product in electronics:
                    print(f"   • {product.name} - €{product.price}")

                # Ricerca per fascia di prezzo
                print(f"\n🔍 Prodotti tra €100 e €300:")
                mid_range = self.product_repo.find_by_price_range(100, 300)
                for product in mid_range:
                    print(f"   • {product.name} - €{product.price}")

                # Aggiornamento prezzo
                if all_products:
                    product_to_update = all_products[0]
                    print(f"\n✏️  Scontando {product_to_update.name}...")
                    new_price = product_to_update.price * 0.9  # 10% di sconto
                    updated_product = self.product_repo.update(product_to_update.id, {
                        'price': round(new_price, 2)
                    })
                    if updated_product:
                        print(f"   ✅ Nuovo prezzo: €{updated_product.price}")

            except Exception as e:
                logger.error(f"Errore demo prodotti: {e}")
                print(f"❌ Errore: {e}")

    def demo_transactions(self):
        """Dimostra l'uso delle transazioni"""
        print("\n" + "=" * 50)
        print("🔄 DEMO TRANSAZIONI")
        print("=" * 50)

        with self.db_manager as db:
            try:
                initial_user_count = self.user_repo.count()
                print(f"👥 Utenti iniziali: {initial_user_count}")

                # Transazione che fallisce
                print(f"\n🚫 Test transazione che fallisce...")
                try:
                    with db.transaction():
                        # Inserisce un utente valido
                        user1 = self.user_repo.create(User("Test User 1", "test1@transaction.com", 25))
                        print(f"   ✅ Creato: {user1.name}")

                        # Cerca di inserire un duplicato per forzare errore
                        user2 = User("Test User 2", "test1@transaction.com", 30)  # Email duplicata
                        self.user_repo.create(user2)

                except Exception as e:
                    print(f"   ❌ Transazione fallita (come previsto): {type(e).__name__}")

                final_user_count = self.user_repo.count()
                print(f"👥 Utenti finali: {final_user_count}")

                if final_user_count == initial_user_count:
                    print("   ✅ Rollback eseguito correttamente!")
                else:
                    print("   ❌ Rollback potrebbe non aver funzionato")

                # Transazione che riesce
                print(f"\n✅ Test transazione che riesce...")
                try:
                    with db.transaction():
                        user1 = self.user_repo.create(User("Transaction User 1", "trans1@example.com", 25))
                        user2 = self.user_repo.create(User("Transaction User 2", "trans2@example.com", 30))
                        print(f"   ✅ Creati: {user1.name} e {user2.name}")

                    print("   ✅ Transazione completata con successo!")

                except Exception as e:
                    print(f"   ❌ Errore inaspettato: {e}")

            except Exception as e:
                logger.error(f"Errore demo transazioni: {e}")
                print(f"❌ Errore: {e}")

    def demo_statistics(self):
        """Mostra statistiche sui dati"""
        print("\n" + "=" * 50)
        print("📊 STATISTICHE FINALI")
        print("=" * 50)

        with self.db_manager as db:
            try:
                # Statistiche utenti
                user_count = self.user_repo.count()
                print(f"👥 Totale utenti: {user_count}")

                if user_count > 0:
                    # Età media (query raw)
                    avg_age_result = db.select_one(
                        "SELECT AVG(age) as avg_age FROM users WHERE age IS NOT NULL"
                    )
                    if avg_age_result and avg_age_result['avg_age']:
                        print(f"📈 Età media: {avg_age_result['avg_age']:.1f} anni")

                    # Utenti per fascia d'età
                    age_groups = db.select("""
                        SELECT 
                            CASE 
                                WHEN age < 30 THEN 'Under 30'
                                WHEN age BETWEEN 30 AND 40 THEN '30-40'
                                ELSE 'Over 40'
                            END as age_group,
                            COUNT(*) as count
                        FROM users 
                        WHERE age IS NOT NULL
                        GROUP BY age_group
                    """)

                    print("📊 Distribuzione età:")
                    for group in age_groups:
                        print(f"   • {group['age_group']}: {group['count']} utenti")

                # Statistiche prodotti
                product_count = self.product_repo.count()
                print(f"\n🛒 Totale prodotti: {product_count}")

                if product_count > 0:
                    # Prezzo medio
                    avg_price_result = db.select_one(
                        "SELECT AVG(price) as avg_price FROM products"
                    )
                    if avg_price_result:
                        print(f"💰 Prezzo medio: €{avg_price_result['avg_price']:.2f}")

                    # Prodotti per categoria
                    categories = db.select("""
                        SELECT category, COUNT(*) as count, AVG(price) as avg_price
                        FROM products 
                        WHERE category IS NOT NULL
                        GROUP BY category
                        ORDER BY count DESC
                    """)

                    print("📊 Prodotti per categoria:")
                    for cat in categories:
                        print(f"   • {cat['category']}: {cat['count']} prodotti (media €{cat['avg_price']:.2f})")

            except Exception as e:
                logger.error(f"Errore statistiche: {e}")
                print(f"❌ Errore: {e}")

    def cleanup_demo_data(self):
        """Pulisce i dati di demo (opzionale)"""
        print("\n🧹 Pulizia dati demo...")

        with self.db_manager as db:
            try:
                # Elimina utenti di test
                test_emails = [
                    'mario@example.com', 'luigi@example.com',
                    'anna@example.com', 'paolo@example.com',
                    'trans1@example.com', 'trans2@example.com'
                ]

                deleted_users = 0
                for email in test_emails:
                    user = self.user_repo.find_by_email(email)
                    if user:
                        if self.user_repo.delete(user.id):
                            deleted_users += 1

                print(f"   ✅ Eliminati {deleted_users} utenti")

                # Elimina tutti i prodotti (per questo demo)
                deleted_products = 0
                all_products = self.product_repo.find_all()
                for product in all_products:
                    if self.product_repo.delete(product.id):
                        deleted_products += 1

                print(f"   ✅ Eliminati {deleted_products} prodotti")

            except Exception as e:
                logger.error(f"Errore pulizia: {e}")
                print(f"❌ Errore pulizia: {e}")

    def run(self):
        """Esegue l'applicazione completa"""
        try:
            print(f"\n🚀 Avvio {APP_NAME} v{VERSION}")
            print("=" * 60)

            # Inizializza
            self.initialize()
            self.setup_database()

            # Esegui demo
            self.demo_users()
            self.demo_products()
            self.demo_transactions()
            self.demo_statistics()

            # Opzionale: pulisci dati
            # self.cleanup_demo_data()

            print("\n" + "=" * 60)
            print("✅ DEMO COMPLETATO CON SUCCESSO!")
            print("=" * 60)

        except Exception as e:
            logger.error(f"Errore applicazione: {e}")
            print(f"\n❌ ERRORE CRITICO: {e}")
            raise


def main():
    """Funzione principale"""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()