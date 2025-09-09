from core.mssql_manager import MSSQLCRUD
from core.mysql_manager import MySQLCRUD
from core.sqlite_manager import SQLiteCRUD
import os

# Soluzione: spostare tutto il codice DENTRO il blocco with
with SQLiteCRUD("esempio.db") as db:
    # Mostra i percorsi che verranno utilizzati - DENTRO il with
    print(f"Database salvato in: {db.db_path}")
    print(f"Cartella instance: {db.instance_dir}")

    # Crea una tabella di esempio
    db.create_table(
        "users",
        {
            "id": "INTEGER",
            "name": "TEXT NOT NULL",
            "email": "TEXT UNIQUE NOT NULL",
            "age": "INTEGER",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        },
        primary_key="id"
    )

    # Controlla se gli utenti esistono già per evitare errori di UNIQUE constraint
    existing_users = db.select("users", where="email IN (?, ?)",
                               params=("mario.rossi@email.com", "luigi.bianchi@email.com"))

    if not existing_users:
        # Inserisce alcuni utenti solo se non esistono già
        user1_id = db.insert("users", {
            "name": "Mario Rossi",
            "email": "mario.rossi@email.com",
            "age": 30
        })

        user2_id = db.insert("users", {
            "name": "Luigi Bianchi",
            "email": "luigi.bianchi@email.com",
            "age": 25
        })
        print(f"Utenti inseriti con ID: {user1_id}, {user2_id}")
    else:
        print("Utenti già esistenti nel database")
        user1_id = existing_users[0]['id'] if len(existing_users) > 0 else None
        user2_id = existing_users[1]['id'] if len(existing_users) > 1 else None

    # Seleziona tutti gli utenti
    all_users = db.select("users")
    print("Tutti gli utenti:", all_users)

    # Seleziona un utente per ID (se esiste)
    if user1_id:
        user = db.select_by_id("users", user1_id)
        print("Utente trovato:", user)

        # Aggiorna un utente
        updated = db.update_by_id("users", user1_id, {"age": 31})
        print(f"Utente aggiornato: {updated}")

    # Conta gli utenti
    user_count = db.count("users")
    print(f"Numero totale di utenti: {user_count}")

    # Backup della tabella
    backup_success = db.backup_table("users", "users_backup.json")
    if backup_success:
        backup_path = os.path.join(db.instance_dir, "users_backup.json")
        print(f"File di backup salvato in: {backup_path}")
# with MSSQLCRUD("localhost\\SQLEXPRESS", "TestDB", "username", "password") as db:
#
#         # Mostra i percorsi che verranno utilizzati per i backup
#         print(f"Cartella instance per backup: {db.instance_dir}")
#
#         # Crea una tabella di esempio
#         db.create_table(
#             "users",
#             {
#                 "id": "INT IDENTITY(1,1)",
#                 "name": "NVARCHAR(100) NOT NULL",
#                 "email": "NVARCHAR(255) UNIQUE NOT NULL",
#                 "age": "INT",
#                 "created_at": "DATETIME2 DEFAULT GETDATE()"
#             },
#             primary_key="id"
#         )
#
#         # Controlla se gli utenti esistono già
#         existing_users = db.select("users", where="email IN (?, ?)",
#                                    params=("mario.rossi@email.com", "luigi.bianchi@email.com"))
#
#         if not existing_users:
#             # Inserisce alcuni utenti
#             user1_id = db.insert("users", {
#                 "name": "Mario Rossi",
#                 "email": "mario.rossi@email.com",
#                 "age": 30
#             })
#
#             user2_id = db.insert("users", {
#                 "name": "Luigi Bianchi",
#                 "email": "luigi.bianchi@email.com",
#                 "age": 25
#             })
#             print(f"Utenti inseriti con ID: {user1_id}, {user2_id}")
#         else:
#             print("Utenti già esistenti nel database")
#             user1_id = existing_users[0]['id'] if len(existing_users) > 0 else None
#
#         # Seleziona tutti gli utenti
#         all_users = db.select("users")
#         print("Tutti gli utenti:", all_users)
#
#         # Seleziona un utente per ID
#         if user1_id:
#             user = db.select_by_id("users", user1_id)
#             print("Utente trovato:", user)
#
#             # Aggiorna un utente
#             updated = db.update_by_id("users", user1_id, {"age": 31})
#             print(f"Utente aggiornato: {updated}")
#
#         # Conta gli utenti
#         user_count = db.count("users")
#         print(f"Numero totale di utenti: {user_count}")
#
#         # Backup della tabella
#         backup_success = db.backup_table("users", "users_backup_mssql.json")
#         if backup_success:
#             backup_path = os.path.join(db.instance_dir, "users_backup_mssql.json")
#             print(f"File di backup salvato in: {backup_path}")
# with MySQLCRUD("localhost", "testdb", "username", "password") as db:
#
#         # Mostra i percorsi che verranno utilizzati per i backup
#         print(f"Cartella instance per backup: {db.instance_dir}")
#
#         # Crea una tabella di esempio
#         db.create_table(
#             "users",
#             {
#                 "id": "INT AUTO_INCREMENT",
#                 "name": "VARCHAR(100) NOT NULL",
#                 "email": "VARCHAR(255) UNIQUE NOT NULL",
#                 "age": "INT",
#                 "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
#             },
#             primary_key="id"
#         )
#
#         # Controlla se gli utenti esistono già
#         existing_users = db.select("users", where="email IN (%s, %s)",
#                                    params=("mario.rossi@email.com", "luigi.bianchi@email.com"))
#
#         if not existing_users:
#             # Inserisce alcuni utenti
#             user1_id = db.insert("users", {
#                 "name": "Mario Rossi",
#                 "email": "mario.rossi@email.com",
#                 "age": 30
#             })
#
#             user2_id = db.insert("users", {
#                 "name": "Luigi Bianchi",
#                 "email": "luigi.bianchi@email.com",
#                 "age": 25
#             })
#             print(f"Utenti inseriti con ID: {user1_id}, {user2_id}")
#         else:
#             print("Utenti già esistenti nel database")
#             user1_id = existing_users[0]['id'] if len(existing_users) > 0 else None
#
#         # Seleziona tutti gli utenti
#         all_users = db.select("users")
#         print("Tutti gli utenti:", all_users)
#
#         # Seleziona un utente per ID
#         if user1_id:
#             user = db.select_by_id("users", user1_id)
#             print("Utente trovato:", user)
#
#             # Aggiorna un utente
#             updated = db.update_by_id("users", user1_id, {"age": 31})
#             print(f"Utente aggiornato: {updated}")
#
#         # Conta gli utenti
#         user_count = db.count("users")
#         print(f"Numero totale di utenti: {user_count}")
#
#         # Crea un indice sulla colonna email
#         db.create_index("users", "idx_email", ["email"], unique=True)
#
#         # Backup della tabella
#         backup_success = db.backup_table("users", "users_backup_mysql.json")
#         if backup_success:
#             backup_path = os.path.join(db.instance_dir, "users_backup_mysql.json")
#             print(f"File di backup salvato in: {backup_path}")


print("Operazioni completate con successo!")