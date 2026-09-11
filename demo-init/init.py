#!/usr/bin/env python3
"""Bootstrap delle site key demo su capjs, parlando con la sua API HTTP.

cap.js v3 non ha piu' uno storage SQLite locale (e' su Redis/Valkey), quindi
questo script non puo' piu' scrivere direttamente nel database come faceva
in precedenza: usa /auth/login + /server/keys, come farebbe la dashboard.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.request

CAPJS_URL = os.environ.get("CAPJS_URL", "http://capjs:3000").rstrip("/")
ADMIN_KEY = os.environ["ADMIN_KEY"]
KEYS_FILE = "/shared/keys.json"
SITE_NAME = "flask-test"
# Seconda chiave, con tokenTTL molto breve: usata dalla pagina /errori di
# demo001 per rendere osservabile la scadenza di un token senza dover
# attendere i 2 minuti della configurazione normale.
SITE_NAME_SHORT_TTL = "flask-test-shortttl"

os.makedirs(os.path.dirname(KEYS_FILE), exist_ok=True)


def request(method, path, body=None, token=None):
    url = f"{CAPJS_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise SystemExit(f"❌ {method} {path} -> HTTP {e.code}: {detail}")


def wait_for_capjs():
    print(f"⏳ Attendo che capjs risponda su {CAPJS_URL}...")
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{CAPJS_URL}/", timeout=2)
            return
        except urllib.error.HTTPError:
            # una risposta HTTP, anche non 2xx, vuol dire che il server e' su
            return
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(1)
    raise SystemExit(f"❌ capjs non raggiungibile: {CAPJS_URL}")


def login():
    res = request("POST", "/auth/login", {"admin_key": ADMIN_KEY})
    if not res.get("success"):
        raise SystemExit("❌ Login su capjs fallito: ADMIN_KEY errata?")
    payload = {"token": res["session_token"], "hash": res["hashed_token"]}
    return base64.b64encode(json.dumps(payload).encode()).decode()


def crea_chiave(token, nome, token_ttl):
    print(f"🆕 Creo nuova chiave per '{nome}'")
    created = request("POST", "/server/keys", {"name": nome}, token=token)
    site_key = created["siteKey"]

    request(
        "PUT",
        f"/server/keys/{site_key}/config",
        {
            "difficulty": 4,
            "challengeCount": 50,
            "expiresMS": 60000,
            "tokenTTL": token_ttl,
        },
        token=token,
    )

    return site_key, created["secretKey"]


wait_for_capjs()

if os.path.exists(KEYS_FILE):
    print(f"✅ Chiavi gia' presenti in {KEYS_FILE}")
    data = json.load(open(KEYS_FILE))
else:
    token = login()

    site_key, secret_key = crea_chiave(token, SITE_NAME, token_ttl=120000)
    # 10 secondi: abbastanza breve da dimostrare la scadenza di un token in
    # una demo interattiva, senza i 2 minuti della chiave principale.
    site_key_short, secret_key_short = crea_chiave(
        token, SITE_NAME_SHORT_TTL, token_ttl=10000
    )

    data = {
        "siteKey": site_key,
        "secretKey": secret_key,
        "siteKeyShortTTL": site_key_short,
        "secretKeyShortTTL": secret_key_short,
    }
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

print(f"💾 Chiavi salvate in {KEYS_FILE}")
print(json.dumps(data, indent=2))
