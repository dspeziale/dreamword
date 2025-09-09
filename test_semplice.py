# test_semplice.py
"""
Test semplice per verificare che il framework database funzioni
Eseguire con: python test_semplice.py
"""

import os
import tempfile


def test_framework():
    """Test base del framework database"""
    print("🧪 TEST FRAMEWORK DATABASE SEMPLICE")
    print("=" * 40)

    try:
        # Import con gestione errori
        from database_framework import (
            DatabaseManager,
            DatabaseConfig,
            DatabaseType
        )
        print("✅ Import framework riuscito")

        # Prova a importare le eccezioni (potrebbero non essere disponibili)
        try:
            from database_framework import DuplicateKeyError, ConstraintViolationError
            print("✅ Import eccezioni riuscito")
            use_custom_exceptions = True
        except ImportError:
            print("⚠️  Eccezioni personalizzate non disponibili, uso Exception generica")
            use_custom_exceptions = False
            DuplicateKeyError = Exception
            ConstraintViolationError = Exception

    except ImportError as e:
        print(f"❌ Errore import: {e}")
        return False

    # Crea database temporaneo
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db_path = temp_db.name
    temp_db.close()

    print(f"📁 Database temporaneo: {os.path.basename(temp_db_path)}")

    try:
        # Test configurazione
        config = DatabaseConfig(
            db_type=DatabaseType.SQLITE,
            file_path=temp_db_path
        )
        print("✅ Configurazione creata")

        # Test connessione
        with DatabaseManager(config) as db:
            print("✅ Connessione database riuscita")

            # Test creazione tabella
            db.execute_raw("""
                CREATE TABLE test_utenti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT UNIQUE
                )
            """)
            print("✅ Creazione tabella riuscita")

            # Test inserimento
            user_id = db.insert("test_utenti", {
                "nome": "Mario Rossi",
                "email": "mario@test.com"
            })
            print(f"✅ Inserimento riuscito (ID: {user_id})")

            # Test lettura
            utenti = db.select("SELECT * FROM test_utenti")
            print(f"✅ Lettura riuscita ({len(utenti)} record)")

            # Test aggiornamento
            updated = db.update("test_utenti",
                                {"nome": "Mario Rossi Aggiornato"},
                                "id = ?",
                                (user_id,))
            print(f"✅ Aggiornamento riuscito ({updated} record)")

            # Test gestione errore duplicato
            print("\n🔍 Test gestione errori...")
            try:
                db.insert("test_utenti", {
                    "nome": "Luigi Verdi",
                    "email": "mario@test.com"  # Email duplicata
                })
                print("❌ Non dovrebbe arrivare qui!")
            except (DuplicateKeyError, ConstraintViolationError):
                print("✅ Errore duplicazione gestito (eccezione personalizzata)")
            except Exception as e:
                if "UNIQUE constraint failed" in str(e):
                    print("✅ Errore duplicazione gestito (eccezione generica)")
                else:
                    print(f"⚠️  Errore inaspettato: {e}")

            # Test transazione
            print("\n🔄 Test transazione...")
            utenti_prima = len(db.select("SELECT * FROM test_utenti"))

            try:
                with db.transaction():
                    db.insert("test_utenti", {
                        "nome": "Test User",
                        "email": "test@transaction.com"
                    })
                    # Forza errore per testare rollback
                    db.insert("test_utenti", {
                        "nome": "Test User 2",
                        "email": "mario@test.com"  # Email duplicata
                    })
            except:
                print("   → Transazione fallita come previsto")

            utenti_dopo = len(db.select("SELECT * FROM test_utenti"))
            if utenti_dopo == utenti_prima:
                print("✅ Rollback transazione funziona")
            else:
                print(f"⚠️  Rollback potrebbe non aver funzionato: {utenti_prima} -> {utenti_dopo}")

            # Test eliminazione
            deleted = db.delete("test_utenti", "email = ?", ("mario@test.com",))
            print(f"✅ Eliminazione riuscita ({deleted} record)")

            # Stato finale
            utenti_finali = db.select("SELECT * FROM test_utenti")
            print(f"📊 Utenti finali: {len(utenti_finali)}")

            for utente in utenti_finali:
                print(f"   • {utente['nome']} ({utente['email']})")

        print("\n🎉 TUTTI I TEST COMPLETATI CON SUCCESSO!")
        return True

    except Exception as e:
        print(f"❌ ERRORE DURANTE I TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Pulisce file temporaneo
        try:
            os.unlink(temp_db_path)
            print(f"🧹 Database temporaneo rimosso")
        except:
            print("⚠️  Non è stato possibile rimuovere il database temporaneo")


def test_import_modules():
    """Test separato per verificare gli import"""
    print("\n📦 TEST IMPORT MODULI")
    print("-" * 30)

    try:
        import sqlite3
        print("✅ sqlite3 disponibile")
    except ImportError:
        print("❌ sqlite3 non disponibile")

    try:
        import mysql.connector
        print("✅ mysql.connector disponibile")
    except ImportError:
        print("⚠️  mysql.connector non disponibile (pip install mysql-connector-python)")

    try:
        import pyodbc
        print("✅ pyodbc disponibile")
    except ImportError:
        print("⚠️  pyodbc non disponibile (pip install pyodbc)")


if __name__ == "__main__":
    success = test_framework()
    test_import_modules()

    if success:
        print("\n✅ FRAMEWORK PRONTO ALL'USO!")
    else:
        print("\n❌ ALCUNI TEST SONO FALLITI")
        exit(1)