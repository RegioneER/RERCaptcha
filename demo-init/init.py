#!/usr/bin/env python3
"""Bootstrap di una site key demo su capjs, parlando con la sua API HTTP.

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


wait_for_capjs()

if os.path.exists(KEYS_FILE):
    print(f"✅ Chiave gia' presente per '{SITE_NAME}'")
    data = json.load(open(KEYS_FILE))
else:
    print(f"🆕 Creo nuova chiave per '{SITE_NAME}'")
    token = login()

    created = request("POST", "/server/keys", {"name": SITE_NAME}, token=token)
    site_key = created["siteKey"]

    request(
        "PUT",
        f"/server/keys/{site_key}/config",
        {
            "difficulty": 4,
            "challengeCount": 50,
            "expiresMS": 60000,
            "tokenTTL": 120000,
        },
        token=token,
    )

    data = {"siteKey": site_key, "secretKey": created["secretKey"]}
    with open(KEYS_FILE, "w") as f:
        json.dump(data, f, indent=2)

print(f"💾 Chiavi salvate in {KEYS_FILE}")
print(json.dumps(data, indent=2))
