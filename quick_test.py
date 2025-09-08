# ==============================================================================
# quick_test_fixed.py - Test Corretto (NON per pytest)
# ==============================================================================

"""
Test semplificato per verificare il framework.
IMPORTANTE: Esegui con: python quick_test_fixed.py
NON con pytest!
"""


def test_import():
    """Test import del framework"""
    print("🔍 Test import ModularFramework...")
    try:
        from framework import ModularFramework
        print("✅ Import ModularFramework: OK")
        return ModularFramework
    except Exception as e:
        print(f"❌ Import fallito: {e}")
        return None


def test_initialization(ModularFramework):
    """Test inizializzazione framework"""
    if not ModularFramework:
        return None

    print("🔍 Test inizializzazione...")
    try:
        fw = ModularFramework()
        print(f"✅ Inizializzazione: OK")
        return fw
    except Exception as e:
        print(f"❌ Inizializzazione fallita: {e}")
        return None


def test_database(fw):
    """Test database"""
    if not fw:
        return False

    print("🔍 Test database...")
    try:
        fw.setup_database()
        print("✅ Database setup: OK")

        # Test connessione
        with fw.db.get_session() as session:
            result = fw.db.execute_query("SELECT 1 as test")
            if result and result[0].get('test') == 1:
                print("✅ Database connessione: OK")
                return True
            else:
                print("❌ Database test query fallita")
                return False

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


def test_config(fw):
    """Test configurazione"""
    if not fw:
        return False

    print("🔍 Test configurazione...")
    try:
        config = fw.config
        print(f"✅ Config provider: {config.database.provider}")
        print(f"✅ Config debug: {config.debug}")
        return True
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False


def test_components(fw):
    """Test componenti"""
    if not fw:
        return False

    print("🔍 Test componenti...")
    try:
        # Test database manager
        assert fw.db is not None
        print("✅ Database manager: OK")

        # Test HTTP client
        assert fw.http is not None
        print("✅ HTTP client: OK")

        # Test plugin manager
        assert fw.plugins is not None
        print("✅ Plugin manager: OK")

        return True
    except Exception as e:
        print(f"❌ Componenti error: {e}")
        return False


def test_status(fw):
    """Test status framework"""
    if not fw:
        return False

    print("🔍 Test status...")
    try:
        status = fw.get_status()
        print(f"✅ Status framework: {status['framework']['initialized']}")
        return True
    except Exception as e:
        print(f"❌ Status error: {e}")
        return False


def main():
    """Esegue tutti i test in sequenza"""
    print("🧪 Test Framework ModularFramework")
    print("=" * 50)

    success_count = 0
    total_tests = 6

    # Test 1: Import
    ModularFramework = test_import()
    if ModularFramework:
        success_count += 1
    else:
        print("❌ STOP: Import fallito")
        return

    # Test 2: Inizializzazione
    fw = test_initialization(ModularFramework)
    if fw:
        success_count += 1
    else:
        print("❌ STOP: Inizializzazione fallita")
        return

    # Test 3: Database
    if test_database(fw):
        success_count += 1

    # Test 4: Configurazione
    if test_config(fw):
        success_count += 1

    # Test 5: Componenti
    if test_components(fw):
        success_count += 1

    # Test 6: Status
    if test_status(fw):
        success_count += 1

    # Risultati finali
    print("\n" + "=" * 50)
    print(f"📊 Risultati: {success_count}/{total_tests} test passati")

    if success_count >= 4:
        print("🎉 Framework funzionante!")
        print(f"📈 Successo: {(success_count / total_tests) * 100:.1f}%")
    else:
        print("❌ Framework ha problemi")

    print(f"\n💡 Per usare il framework:")
    print(f"   from framework import ModularFramework")
    print(f"   fw = ModularFramework()")
    print(f"   fw.setup_database()")


if __name__ == "__main__":
    main()