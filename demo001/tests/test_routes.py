"""Smoke test delle route della demo.

Non richiede un servizio capjs raggiungibile: copre solo che le pagine si
rendano, non che la verifica funzioni (per quella serve un capjs vero, vedi
la sezione Verifica del piano).
"""

import os
import re
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("SITE_KEY", "test-site-key")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("CAPJS_KEYS_FILE", "/percorso/inesistente/keys.json")

import app as flask_app  # noqa: E402


@pytest.fixture
def client():
    flask_app.app.config["TESTING"] = True
    return flask_app.app.test_client()


@pytest.mark.parametrize(
    "url",
    ["/", "/visible-it", "/visible-en", "/invisible", "/errori", "/guida"],
)
def test_pagine_rispondono(client, url):
    r = client.get(url)
    assert r.status_code == 200, f"{url} -> {r.status_code}"


def test_guida_linka_pagina_errori(client):
    """La guida deve linkare /errori quando la route esiste."""
    html = client.get("/guida").get_data(as_text=True)
    assert 'href="/errori"' in html


def test_guida_contiene_tutte_le_ancore(client):
    """Un link del sommario senza sezione corrispondente passerebbe inosservato."""
    html = client.get("/guida").get_data(as_text=True)
    ancore_link = set(re.findall(r'href="#([a-z-]+)"', html))
    ancore_id = set(re.findall(r'id="([a-z-]+)"', html))
    mancanti = ancore_link - ancore_id
    assert not mancanti, f"Link del sommario senza sezione: {mancanti}"


def test_csp_presente_su_ogni_pagina(client):
    for url in ["/", "/visible-it", "/invisible", "/guida"]:
        r = client.get(url)
        assert "Content-Security-Policy" in r.headers


def test_invio_senza_token_non_e_500(client):
    """Un invio senza captcha risolto deve dare un errore leggibile, non un crash."""
    r = client.post("/visible-it", data={"text": "prova"})
    assert r.status_code == 200
    assert "Errore non previsto" not in r.get_data(as_text=True)
