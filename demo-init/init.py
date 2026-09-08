#!/usr/bin/env python3
import sqlite3, json, os, time, base64, secrets
from argon2 import PasswordHasher

DB_PATH = os.environ.get("CAPJS_DB", "/data/db.sqlite")
KEYS_FILE = "/shared/keys.json"
SITE_NAME = "flask-test"
# Seconda chiave, con tokenTTL molto breve: usata dalla pagina /errori di
# demo001 per rendere osservabile la scadenza di un token senza dover
# attendere i 2 minuti della configurazione normale.
SITE_NAME_SHORT_TTL = "flask-test-shortttl"

os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)

print("⏳ Attendo che il database esista...")
for _ in range(30):
    if os.path.exists(DB_PATH):
        break
    time.sleep(1)
else:
    raise SystemExit("❌ Database non trovato: " + DB_PATH)

# Il file db.sqlite viene creato da capjs alla connessione, PRIMA che le sue
# "create table if not exists" abbiano finito di girare: c'è quindi una
# finestra in cui il file esiste già ma la tabella "keys" no. Con
# `docker compose up` che avvia i servizi in parallelo (o su un disco lento)
# questa finestra può bastare a far fallire la query sottostante con
# "no such table: keys". Si riprova la connessione stessa, non solo
# l'esistenza del file.
print("⏳ Attendo che la tabella 'keys' sia pronta...")
conn = None
for _ in range(30):
    try:
        tentativo = sqlite3.connect(DB_PATH)
        tentativo.execute("SELECT 1 FROM keys LIMIT 1")
        conn = tentativo
        break
    except sqlite3.OperationalError:
        tentativo.close()
        time.sleep(1)
else:
    raise SystemExit("❌ Tabella 'keys' non pronta dopo 30s: " + DB_PATH)

conn.row_factory = sqlite3.Row
cur = conn.cursor()

hasher = PasswordHasher()


def crea_o_recupera_chiave(nome, config):
    """Crea una coppia siteKey/secretKey se non esiste già per `nome`.

    Ritorna sempre (siteKey, secretKey). Se la chiave esiste già ma il
    secretKey non è più leggibile da keys.json (perché mostrato una sola
    volta, come nel servizio vero), la vecchia riga resta orfana: per questa
    demo locale va bene, non è il percorso da seguire in produzione.
    """
    cur.execute("SELECT * FROM keys WHERE name=?", (nome,))
    row = cur.fetchone()

    # TODO: se la chiave non è in key_files, ma sul db va cancellata dal db e
    #       rigenerata
    if row:
        print(f"✅ Chiave già presente per '{nome}'")
        return None

    print(f"🆕 Creo nuova chiave per '{nome}'")
    siteKey = secrets.token_hex(5)
    secretKey = base64.urlsafe_b64encode(secrets.token_bytes(30)).decode().rstrip("=")
    secretHash = hasher.hash(secretKey)

    cur.execute(
        "INSERT INTO keys (siteKey, name, secretHash, config, created) VALUES (?, ?, ?, ?, ?)",
        (siteKey, nome, secretHash, json.dumps(config), int(time.time() * 1000)),
    )
    conn.commit()

    return siteKey, secretKey


if os.path.exists(KEYS_FILE):
    data = json.load(open(KEYS_FILE))
else:
    data = {}

principale = crea_o_recupera_chiave(
    SITE_NAME,
    {
        "difficulty": 4,
        "challengeCount": 50,
        "saltSize": 32,
        "expiresMS": 60000,
        "tokenTTL": 120000,
    },
)
if principale:
    data["siteKey"], data["secretKey"] = principale

breve = crea_o_recupera_chiave(
    SITE_NAME_SHORT_TTL,
    {
        "difficulty": 4,
        "challengeCount": 50,
        "saltSize": 32,
        "expiresMS": 60000,
        # 10 secondi: abbastanza breve da dimostrare la scadenza di un
        # token in una demo interattiva, senza i 2 minuti della chiave
        # principale.
        "tokenTTL": 10000,
    },
)
if breve:
    data["siteKeyShortTTL"], data["secretKeyShortTTL"] = breve

with open(KEYS_FILE, "w") as f:
    json.dump(data, f, indent=2)

print(f"💾 Chiavi salvate in {KEYS_FILE}")
print(json.dumps(data, indent=2))
