# from core.mssql_manager import MSSQLCRUD
# from core.mysql_manager import MySQLCRUD
# from core.sqlite_manager import SQLiteCRUD
# import os
#
# # Soluzione: spostare tutto il codice DENTRO il blocco with
# with SQLiteCRUD("esempio.db") as db:
#     # Mostra i percorsi che verranno utilizzati - DENTRO il with
#     print(f"Database salvato in: {db.db_path}")
#     print(f"Cartella instance: {db.instance_dir}")
#
#     # Crea una tabella di esempio
#     db.create_table(
#         "users",
#         {
#             "id": "INTEGER",
#             "name": "TEXT NOT NULL",
#             "email": "TEXT UNIQUE NOT NULL",
#             "age": "INTEGER",
#             "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
#         },
#         primary_key="id"
#     )
#
#     # Controlla se gli utenti esistono già per evitare errori di UNIQUE constraint
#     existing_users = db.select("users", where="email IN (?, ?)",
#                                params=("mario.rossi@email.com", "luigi.bianchi@email.com"))
#
#     if not existing_users:
#         # Inserisce alcuni utenti solo se non esistono già
#         user1_id = db.insert("users", {
#             "name": "Mario Rossi",
#             "email": "mario.rossi@email.com",
#             "age": 30
#         })
#
#         user2_id = db.insert("users", {
#             "name": "Luigi Bianchi",
#             "email": "luigi.bianchi@email.com",
#             "age": 25
#         })
#         print(f"Utenti inseriti con ID: {user1_id}, {user2_id}")
#     else:
#         print("Utenti già esistenti nel database")
#         user1_id = existing_users[0]['id'] if len(existing_users) > 0 else None
#         user2_id = existing_users[1]['id'] if len(existing_users) > 1 else None
#
#     # Seleziona tutti gli utenti
#     all_users = db.select("users")
#     print("Tutti gli utenti:", all_users)
#
#     # Seleziona un utente per ID (se esiste)
#     if user1_id:
#         user = db.select_by_id("users", user1_id)
#         print("Utente trovato:", user)
#
#         # Aggiorna un utente
#         updated = db.update_by_id("users", user1_id, {"age": 31})
#         print(f"Utente aggiornato: {updated}")
#
#     # Conta gli utenti
#     user_count = db.count("users")
#     print(f"Numero totale di utenti: {user_count}")
#
#     # Backup della tabella
#     backup_success = db.backup_table("users", "users_backup.json")
#     if backup_success:
#         backup_path = os.path.join(db.instance_dir, "users_backup.json")
#         print(f"File di backup salvato in: {backup_path}")
# # with MSSQLCRUD("localhost\\SQLEXPRESS", "TestDB", "username", "password") as db:
# #
# #         # Mostra i percorsi che verranno utilizzati per i backup
# #         print(f"Cartella instance per backup: {db.instance_dir}")
# #
# #         # Crea una tabella di esempio
# #         db.create_table(
# #             "users",
# #             {
# #                 "id": "INT IDENTITY(1,1)",
# #                 "name": "NVARCHAR(100) NOT NULL",
# #                 "email": "NVARCHAR(255) UNIQUE NOT NULL",
# #                 "age": "INT",
# #                 "created_at": "DATETIME2 DEFAULT GETDATE()"
# #             },
# #             primary_key="id"
# #         )
# #
# #         # Controlla se gli utenti esistono già
# #         existing_users = db.select("users", where="email IN (?, ?)",
# #                                    params=("mario.rossi@email.com", "luigi.bianchi@email.com"))
# #
# #         if not existing_users:
# #             # Inserisce alcuni utenti
# #             user1_id = db.insert("users", {
# #                 "name": "Mario Rossi",
# #                 "email": "mario.rossi@email.com",
# #                 "age": 30
# #             })
# #
# #             user2_id = db.insert("users", {
# #                 "name": "Luigi Bianchi",
# #                 "email": "luigi.bianchi@email.com",
# #                 "age": 25
# #             })
# #             print(f"Utenti inseriti con ID: {user1_id}, {user2_id}")
# #         else:
# #             print("Utenti già esistenti nel database")
# #             user1_id = existing_users[0]['id'] if len(existing_users) > 0 else None
# #
# #         # Seleziona tutti gli utenti
# #         all_users = db.select("users")
# #         print("Tutti gli utenti:", all_users)
# #
# #         # Seleziona un utente per ID
# #         if user1_id:
# #             user = db.select_by_id("users", user1_id)
# #             print("Utente trovato:", user)
# #
# #             # Aggiorna un utente
# #             updated = db.update_by_id("users", user1_id, {"age": 31})
# #             print(f"Utente aggiornato: {updated}")
# #
# #         # Conta gli utenti
# #         user_count = db.count("users")
# #         print(f"Numero totale di utenti: {user_count}")
# #
# #         # Backup della tabella
# #         backup_success = db.backup_table("users", "users_backup_mssql.json")
# #         if backup_success:
# #             backup_path = os.path.join(db.instance_dir, "users_backup_mssql.json")
# #             print(f"File di backup salvato in: {backup_path}")
# # with MySQLCRUD("localhost", "testdb", "username", "password") as db:
# #
# #         # Mostra i percorsi che verranno utilizzati per i backup
# #         print(f"Cartella instance per backup: {db.instance_dir}")
# #
# #         # Crea una tabella di esempio
# #         db.create_table(
# #             "users",
# #             {
# #                 "id": "INT AUTO_INCREMENT",
# #                 "name": "VARCHAR(100) NOT NULL",
# #                 "email": "VARCHAR(255) UNIQUE NOT NULL",
# #                 "age": "INT",
# #                 "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
# #             },
# #             primary_key="id"
# #         )
# #
# #         # Controlla se gli utenti esistono già
# #         existing_users = db.select("users", where="email IN (%s, %s)",
# #                                    params=("mario.rossi@email.com", "luigi.bianchi@email.com"))
# #
# #         if not existing_users:
# #             # Inserisce alcuni utenti
# #             user1_id = db.insert("users", {
# #                 "name": "Mario Rossi",
# #                 "email": "mario.rossi@email.com",
# #                 "age": 30
# #             })
# #
# #             user2_id = db.insert("users", {
# #                 "name": "Luigi Bianchi",
# #                 "email": "luigi.bianchi@email.com",
# #                 "age": 25
# #             })
# #             print(f"Utenti inseriti con ID: {user1_id}, {user2_id}")
# #         else:
# #             print("Utenti già esistenti nel database")
# #             user1_id = existing_users[0]['id'] if len(existing_users) > 0 else None
# #
# #         # Seleziona tutti gli utenti
# #         all_users = db.select("users")
# #         print("Tutti gli utenti:", all_users)
# #
# #         # Seleziona un utente per ID
# #         if user1_id:
# #             user = db.select_by_id("users", user1_id)
# #             print("Utente trovato:", user)
# #
# #             # Aggiorna un utente
# #             updated = db.update_by_id("users", user1_id, {"age": 31})
# #             print(f"Utente aggiornato: {updated}")
# #
# #         # Conta gli utenti
# #         user_count = db.count("users")
# #         print(f"Numero totale di utenti: {user_count}")
# #
# #         # Crea un indice sulla colonna email
# #         db.create_index("users", "idx_email", ["email"], unique=True)
# #
# #         # Backup della tabella
# #         backup_success = db.backup_table("users", "users_backup_mysql.json")
# #         if backup_success:
# #             backup_path = os.path.join(db.instance_dir, "users_backup_mysql.json")
# #             print(f"File di backup salvato in: {backup_path}")
#
#
# print("Operazioni completate con successo!")

"""
Esempio di integrazione della cache OUI con Flask.
API REST per lookup MAC address e gestione cache OUI.
"""

from flask import Flask, request, jsonify, render_template_string
import os
import re
from datetime import datetime
from core.oui_cache_system import OUICache

app = Flask(__name__)

# Configurazione
app.config['OUI_CACHE_INSTANCE'] = os.path.join(app.instance_path, 'oui_cache')

# Inizializza cache OUI globale
oui_cache = None


def get_oui_cache():
    """Ottiene istanza cache OUI (lazy loading)."""
    global oui_cache
    if oui_cache is None:
        cache_dir = app.config['OUI_CACHE_INSTANCE']
        os.makedirs(cache_dir, exist_ok=True)
        oui_cache = OUICache(cache_dir)
    return oui_cache


def validate_mac_address(mac):
    """Valida formato MAC address."""
    # Pattern per vari formati MAC
    patterns = [
        r'^[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}$',
        r'^[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}$',
        r'^[0-9A-Fa-f]{12}$',
        r'^[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}$'
    ]

    return any(re.match(pattern, mac.strip()) for pattern in patterns)


@app.route('/')
def index():
    """Pagina principale con interfaccia web."""
    html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>OUI MAC Address Lookup</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 8px; margin: 20px 0; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #0056b3; }
        .result { margin-top: 20px; padding: 15px; border-radius: 4px; }
        .result.success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
        .result.error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .stats { background: #e9ecef; padding: 15px; border-radius: 4px; margin: 20px 0; }
        .api-info { background: #fff3cd; padding: 15px; border-radius: 4px; margin: 20px 0; }
        code { background: #f8f9fa; padding: 2px 4px; border-radius: 2px; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>🔍 OUI MAC Address Lookup</h1>

    <div class="container">
        <h2>Cerca Vendor MAC Address</h2>
        <form id="macForm">
            <div class="form-group">
                <label for="mac">MAC Address:</label>
                <input type="text" id="mac" name="mac" placeholder="es: 00:50:56:12:34:56 o 005056123456" required>
            </div>
            <button type="submit">🔍 Cerca</button>
        </form>
        <div id="macResult"></div>
    </div>

    <div class="container">
        <h2>Cerca per Vendor</h2>
        <form id="vendorForm">
            <div class="form-group">
                <label for="vendor">Nome Vendor:</label>
                <input type="text" id="vendor" name="vendor" placeholder="es: Apple, Cisco, Intel" required>
            </div>
            <button type="submit">🔍 Cerca</button>
        </form>
        <div id="vendorResult"></div>
    </div>

    <div class="stats">
        <h2>📊 Statistiche Cache</h2>
        <div id="cacheStats">Caricamento...</div>
        <button onclick="updateCache()">🔄 Aggiorna Cache</button>
    </div>

    <div class="api-info">
        <h2>📡 API Endpoints</h2>
        <p><strong>GET</strong> <code>/api/lookup/&lt;mac_address&gt;</code> - Lookup MAC address</p>
        <p><strong>GET</strong> <code>/api/search?vendor=&lt;name&gt;&amp;limit=10</code> - Cerca vendor</p>
        <p><strong>GET</strong> <code>/api/stats</code> - Statistiche cache</p>
        <p><strong>POST</strong> <code>/api/update</code> - Aggiorna cache</p>

        <h3>Esempi:</h3>
        <pre>curl {{ request.url_root }}api/lookup/00:50:56:12:34:56
curl "{{ request.url_root }}api/search?vendor=Apple&limit=5"</pre>
    </div>

    <script>
        // Funzione per gestire lookup MAC
        document.getElementById('macForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const mac = document.getElementById('mac').value;
            const resultDiv = document.getElementById('macResult');

            try {
                const response = await fetch(`/api/lookup/${encodeURIComponent(mac)}`);
                const data = await response.json();

                if (data.success) {
                    resultDiv.innerHTML = `
                        <div class="result success">
                            <h3>✅ Vendor Trovato</h3>
                            <p><strong>Azienda:</strong> ${data.vendor}</p>
                            <p><strong>OUI:</strong> ${data.oui} (${data.oui_hex})</p>
                            <p><strong>MAC:</strong> ${data.mac_queried}</p>
                            ${data.address ? `<p><strong>Indirizzo:</strong> ${data.address}</p>` : ''}
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <h3>❌ ${data.error}</h3>
                            <p>${data.message || 'Vendor non trovato per questo MAC address'}</p>
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error"><h3>❌ Errore di rete</h3></div>`;
            }
        });

        // Funzione per gestire ricerca vendor
        document.getElementById('vendorForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const vendor = document.getElementById('vendor').value;
            const resultDiv = document.getElementById('vendorResult');

            try {
                const response = await fetch(`/api/search?vendor=${encodeURIComponent(vendor)}&limit=10`);
                const data = await response.json();

                if (data.success && data.results.length > 0) {
                    let html = `
                        <div class="result success">
                            <h3>✅ Trovati ${data.results.length} risultati</h3>
                            <ul>
                    `;

                    data.results.forEach(result => {
                        html += `
                            <li>
                                <strong>${result.vendor}</strong><br>
                                OUI: ${result.oui} (${result.oui_hex})
                                ${result.address ? `<br><small>${result.address.substring(0, 100)}${result.address.length > 100 ? '...' : ''}</small>` : ''}
                            </li>
                        `;
                    });

                    html += '</ul></div>';
                    resultDiv.innerHTML = html;
                } else {
                    resultDiv.innerHTML = `
                        <div class="result error">
                            <h3>❌ Nessun risultato</h3>
                            <p>Nessun vendor trovato per "${vendor}"</p>
                        </div>
                    `;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="result error"><h3>❌ Errore di rete</h3></div>`;
            }
        });

        // Carica statistiche cache
        async function loadCacheStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();

                if (data.success) {
                    const stats = data.stats;
                    const lastUpdate = stats.last_update ? new Date(stats.last_update).toLocaleString('it-IT') : 'Mai';

                    document.getElementById('cacheStats').innerHTML = `
                        <p><strong>Record totali:</strong> ${stats.total_records?.toLocaleString() || 0}</p>
                        <p><strong>Dimensione DB:</strong> ${stats.database_size_mb || 0} MB</p>
                        <p><strong>Ultimo aggiornamento:</strong> ${lastUpdate}</p>
                        <p><strong>Età cache:</strong> ${stats.cache_age_days || 0} giorni</p>
                        <p><strong>Stato:</strong> ${stats.needs_update ? '🔴 Aggiornamento necessario' : '🟢 Aggiornata'}</p>
                    `;
                }
            } catch (error) {
                document.getElementById('cacheStats').innerHTML = '<p>❌ Errore caricamento statistiche</p>';
            }
        }

        // Aggiorna cache
        async function updateCache() {
            try {
                const response = await fetch('/api/update', { method: 'POST' });
                const data = await response.json();

                if (data.success) {
                    alert('✅ Cache aggiornata con successo!');
                    loadCacheStats();
                } else {
                    alert(`❌ Errore aggiornamento: ${data.message}`);
                }
            } catch (error) {
                alert('❌ Errore di rete durante aggiornamento');
            }
        }

        // Carica statistiche al caricamento pagina
        loadCacheStats();
    </script>
</body>
</html>
    """
    return render_template_string(html_template)


@app.route('/api/lookup/<mac_address>')
def api_lookup(mac_address):
    """API endpoint per lookup MAC address."""
    try:
        # Valida MAC address
        if not validate_mac_address(mac_address):
            return jsonify({
                'success': False,
                'error': 'MAC address non valido',
                'message': 'Formati supportati: XX:XX:XX:XX:XX:XX, XX-XX-XX-XX-XX-XX, XXXXXXXXXXXX'
            }), 400

        # Cerca nel cache
        cache = get_oui_cache()
        result = cache.lookup_mac(mac_address)

        if result:
            return jsonify({
                'success': True,
                'mac_queried': result['mac_queried'],
                'oui': result['oui'],
                'oui_hex': result['oui_hex'],
                'vendor': result['vendor'],
                'address': result['address']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Vendor non trovato',
                'message': 'MAC address valido ma vendor non trovato nel database OUI'
            }), 404

    except Exception as e:
        app.logger.error(f"Errore lookup MAC {mac_address}: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore interno del server',
            'message': str(e)
        }), 500


@app.route('/api/search')
def api_search():
    """API endpoint per ricerca vendor per nome."""
    try:
        vendor_name = request.args.get('vendor', '').strip()
        limit = int(request.args.get('limit', 10))

        if not vendor_name:
            return jsonify({
                'success': False,
                'error': 'Parametro vendor mancante',
                'message': 'Specificare il parametro ?vendor=nome_vendor'
            }), 400

        if limit < 1 or limit > 100:
            limit = 10

        # Cerca nel cache
        cache = get_oui_cache()
        results = cache.search_vendor(vendor_name, limit)

        return jsonify({
            'success': True,
            'query': vendor_name,
            'results': results,
            'count': len(results)
        })

    except Exception as e:
        app.logger.error(f"Errore ricerca vendor: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore interno del server',
            'message': str(e)
        }), 500


@app.route('/api/stats')
def api_stats():
    """API endpoint per statistiche cache."""
    try:
        cache = get_oui_cache()
        stats = cache.get_cache_stats()

        # Converti datetime in string per JSON
        if stats.get('last_update'):
            stats['last_update'] = stats['last_update'].isoformat()

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        app.logger.error(f"Errore statistiche: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore interno del server',
            'message': str(e)
        }), 500


@app.route('/api/update', methods=['POST'])
def api_update():
    """API endpoint per aggiornare cache."""
    try:
        force = request.json.get('force', False) if request.is_json else False

        cache = get_oui_cache()

        # Aggiorna in background (per evitare timeout lunghi)
        updated = cache.update_cache(force=force)

        if updated:
            stats = cache.get_cache_stats()
            return jsonify({
                'success': True,
                'message': 'Cache aggiornata con successo',
                'total_records': stats.get('total_records', 0)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Cache già aggiornata o errore durante aggiornamento'
            })

    except Exception as e:
        app.logger.error(f"Errore aggiornamento cache: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore interno del server',
            'message': str(e)
        }), 500


@app.route('/api/batch', methods=['POST'])
def api_batch_lookup():
    """API endpoint per lookup batch di MAC addresses."""
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type deve essere application/json'
            }), 400

        mac_addresses = request.json.get('mac_addresses', [])

        if not isinstance(mac_addresses, list) or not mac_addresses:
            return jsonify({
                'success': False,
                'error': 'Array mac_addresses richiesto e non vuoto'
            }), 400

        if len(mac_addresses) > 1000:
            return jsonify({
                'success': False,
                'error': 'Massimo 1000 MAC addresses per batch'
            }), 400

        cache = get_oui_cache()
        results = []
        found_count = 0

        for mac in mac_addresses:
            if validate_mac_address(str(mac)):
                result = cache.lookup_mac(str(mac))
                if result:
                    results.append({
                        'mac': mac,
                        'found': True,
                        'vendor': result['vendor'],
                        'oui': result['oui'],
                        'oui_hex': result['oui_hex'],
                        'address': result['address']
                    })
                    found_count += 1
                else:
                    results.append({
                        'mac': mac,
                        'found': False,
                        'error': 'Vendor non trovato'
                    })
            else:
                results.append({
                    'mac': mac,
                    'found': False,
                    'error': 'MAC address non valido'
                })

        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'total': len(mac_addresses),
                'found': found_count,
                'not_found': len(mac_addresses) - found_count,
                'success_rate': round((found_count / len(mac_addresses)) * 100, 2)
            }
        })

    except Exception as e:
        app.logger.error(f"Errore batch lookup: {e}")
        return jsonify({
            'success': False,
            'error': 'Errore interno del server',
            'message': str(e)
        }), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint non trovato',
        'message': 'L\'endpoint richiesto non esiste'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Errore interno del server',
        'message': 'Si è verificato un errore interno'
    }), 500


if __name__ == '__main__':
    # Crea directory instance se non esiste
    os.makedirs(app.instance_path, exist_ok=True)

    # Inizializza cache all'avvio (opzionale)
    try:
        cache = get_oui_cache()
        cache.update_cache()  # Aggiorna se necessario
        print("✅ Cache OUI inizializzata")
    except Exception as e:
        print(f"⚠️  Avviso: Errore inizializzazione cache OUI: {e}")

    app.run(debug=True, host='0.0.0.0', port=5000)