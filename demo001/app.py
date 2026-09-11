import json
import logging
import os
import secrets
import textwrap
import time
from pathlib import Path

from flask import Flask, render_template, request
from markupsafe import Markup, escape

import capjs_reference
from snippets.verify import CAMPO_TOKEN, verifica_captcha

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

# URL del servizio raggiungibile dal SERVER (rete interna).
CAPJS_INTERNAL_URL = os.environ.get("CAPJS_INTERNAL_URL", "http://capjs:3000")
# URL del servizio raggiungibile dal BROWSER dell'utente.
CAPJS_PUBLIC_URL = os.environ.get("CAPJS_PUBLIC_URL", "http://localhost:3000")

# File in cui demo-init deposita le chiavi generate al primo avvio.
KEYS_FILE = os.environ.get("CAPJS_KEYS_FILE", "/shared/keys.json")


def _leggi_chiavi():
    """Legge le chiavi dalle variabili d'ambiente, con fallback su keys.json.

    In un'installazione reale le chiavi arrivano dall'ambiente. In locale
    vengono generate a runtime da demo-init, che le scrive in un file
    condiviso: leggerlo evita di dover modificare compose.yml a mano prima di
    poter avviare la demo.
    """
    chiavi = {
        "site_key": os.environ.get("SITE_KEY"),
        "secret_key": os.environ.get("SECRET_KEY"),
        "site_key_short_ttl": os.environ.get("SITE_KEY_SHORT_TTL"),
        "secret_key_short_ttl": os.environ.get("SECRET_KEY_SHORT_TTL"),
    }

    if chiavi["site_key"] and chiavi["secret_key"]:
        return chiavi

    try:
        with open(KEYS_FILE) as f:
            dati = json.load(f)
    except (OSError, ValueError) as exc:
        logger.warning("Chiavi non leggibili da %s: %s", KEYS_FILE, exc)
        return chiavi

    chiavi["site_key"] = chiavi["site_key"] or dati.get("siteKey")
    chiavi["secret_key"] = chiavi["secret_key"] or dati.get("secretKey")
    chiavi["site_key_short_ttl"] = chiavi["site_key_short_ttl"] or dati.get(
        "siteKeyShortTTL"
    )
    chiavi["secret_key_short_ttl"] = chiavi["secret_key_short_ttl"] or dati.get(
        "secretKeyShortTTL"
    )
    return chiavi


_chiavi = _leggi_chiavi()
CAPJS_SITE_KEY = _chiavi["site_key"]
CAPJS_SECRET = _chiavi["secret_key"]
# Seconda coppia di chiavi con tokenTTL molto breve, usata dalla pagina degli
# scenari di errore per rendere osservabile la scadenza di un token.
CAPJS_SITE_KEY_SHORT_TTL = _chiavi["site_key_short_ttl"]
CAPJS_SECRET_SHORT_TTL = _chiavi["secret_key_short_ttl"]

CONFIGURAZIONE_MANCANTE = not (CAPJS_SITE_KEY and CAPJS_SECRET)
if CONFIGURAZIONE_MANCANTE:
    logger.error(
        "SITE_KEY/SECRET_KEY non configurate e %s non leggibile. "
        "Le pagine con captcha mostreranno un avviso.",
        KEYS_FILE,
    )

# La pagina /errori invia deliberatamente secret errati, il che fa bloccare
# per 250 ms l'IP di questo server. Va tenuta fuori dalla produzione: per
# default la si abilita solo quando il servizio non è raggiunto via https.
DEMO_ERRORI_ENABLED = os.environ.get(
    "DEMO_ERRORI_ENABLED",
    "false" if CAPJS_PUBLIC_URL.startswith("https") else "true",
).lower() in ("1", "true", "yes")


app = Flask(__name__)


def get_random_urlsafe_string(length):
    return secrets.token_urlsafe(length)[:length]


def configure_app_headers(app):
    def _make_nonce():
        if not getattr(request, "csp_nonce", None):
            request.csp_nonce = get_random_urlsafe_string(18)

    def _add_security_headers(response):
        nonce = getattr(request, "csp_nonce", "")
        # Content Security Policy.
        #
        # Questa è deliberatamente la stessa policy consigliata agli
        # integratori in /guida#csp: se qui fosse più permissiva, la guida
        # documenterebbe qualcosa che nessuno ha mai provato.
        #
        # - default-src 'self'   tutto ciò che non è indicato sotto resta
        #                        limitato all'origine della pagina
        # - script-src           il nonce copre gli script propri, anche
        #                        esterni; l'origine del servizio serve perché
        #                        widget.js inietta a sua volta uno script
        # - 'wasm-unsafe-eval'   necessario per compilare il modulo WebAssembly
        # - worker-src blob:     il solver gira in worker creati da blob
        # - connect-src          challenge e redeem sono fetch cross-origin
        # - style-src            il nonce vale anche per lo <style> che il
        #                        widget inietta nel proprio shadow DOM, grazie
        #                        a window.CAP_CSS_NONCE impostata in
        #                        partials/loader.html
        response.headers["Content-Security-Policy"] = "; ".join(
            [
                "default-src 'self'",
                f"script-src 'nonce-{nonce}' {CAPJS_PUBLIC_URL} 'wasm-unsafe-eval'",
                f"style-src 'self' 'nonce-{nonce}'",
                f"connect-src 'self' {CAPJS_PUBLIC_URL}",
                "img-src 'self' data:",
                "worker-src blob:",
                "object-src 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "frame-ancestors 'none'",
            ]
        )
        # Impedisce l'inserimento del sito in iframe (previene il clickjacking).
        response.headers["X-Frame-Options"] = "DENY"
        # Evita che dati sensibili restino nella cache del browser.
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, max-age=0"
        )
        # HSTS, solo dove il traffico è già su https.
        if CAPJS_PUBLIC_URL.startswith("https"):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        # Impedisce al browser di indovinare il MIME type.
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Limita le informazioni inviate nel referer.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # Limita l'accesso alle API del browser.
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=()"
        )
        return response

    app.before_request(_make_nonce)
    app.after_request(_add_security_headers)


configure_app_headers(app)


# --- Resa del codice in pagina ---------------------------------------------

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import get_lexer_by_name

    _PYGMENTS = True
except ImportError:  # pragma: no cover - l'evidenziazione è un di più
    _PYGMENTS = False


@app.template_filter("evidenzia")
def evidenzia(sorgente, lang="text"):
    """Normalizza e rende un blocco di codice.

    `sorgente` può essere una stringa qualsiasi oppure il Markup catturato da
    {% set x %}{% include ... %}{% endset %}. In quel secondo caso ogni
    {{ variabile }} presente nel partial incluso è già stata sottoposta
    all'autoescape di Jinja (es. "<NONCE>" diventa "&lt;NONCE&gt;"): va
    decodificata con Markup.unescape() PRIMA di passarla a Pygments, che la
    tratta come sorgente da evidenziare e la escaperebbe di nuovo, producendo
    un doppio escaping ("&amp;lt;NONCE&amp;gt;") invece del testo originale.
    """
    if isinstance(sorgente, Markup):
        testo = sorgente.unescape()
    else:
        testo = str(sorgente)
    testo = textwrap.dedent(testo).strip()

    if _PYGMENTS and lang != "text":
        try:
            lexer = get_lexer_by_name(lang)
        except Exception:
            return Markup(escape(testo))
        # nowrap: solo i token, senza il <div class="highlight"><pre> di
        # Pygments, che duplicherebbe il <pre> della macro.
        return Markup(highlight(testo, lexer, HtmlFormatter(nowrap=True)).rstrip("\n"))

    return Markup(escape(testo))


def carica_snippet(nome):
    """Legge un file da snippets/ per mostrarlo nella guida."""
    percorso = BASE_DIR / "snippets" / nome
    try:
        return percorso.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - solo se il file sparisce
        logger.error("Snippet %s non leggibile: %s", nome, exc)
        return f"# snippet non disponibile: {nome}"


def has_endpoint(nome):
    """Permette ai template di linkare una route solo se esiste già.

    Usato dalla guida per il link alla pagina degli scenari di errore,
    aggiunta in una fase successiva del lavoro sulla demo.
    """
    return nome in app.view_functions


app.jinja_env.globals.update(
    carica_snippet=carica_snippet,
    riferimenti=capjs_reference,
    campo_token=CAMPO_TOKEN,
    has_endpoint=has_endpoint,
)


@app.context_processor
def _contesto_comune():
    """Valori disponibili in ogni template."""
    return {
        "capjs_public_url": CAPJS_PUBLIC_URL,
        "site_key": CAPJS_SITE_KEY,
        "csp_nonce": getattr(request, "csp_nonce", ""),
        "configurazione_mancante": CONFIGURAZIONE_MANCANTE,
        "demo_errori_enabled": DEMO_ERRORI_ENABLED,
        "localizzato": True,
    }


# --- Route -----------------------------------------------------------------


def _gestisci_invio(template, **contesto):
    """Gestisce GET e POST di una pagina demo.

    Le pagine differiscono solo per il template: la verifica del token è la
    stessa, ed è quella di snippets/verify.py, cioè l'esempio pubblicato
    nella guida.
    """
    esito = None

    if request.method == "POST":
        token = request.form.get(CAMPO_TOKEN)
        ok, status, body, errore = verifica_captcha(
            CAPJS_INTERNAL_URL, CAPJS_SITE_KEY, CAPJS_SECRET, token
        )
        esito = {
            "ok": ok,
            "status": status,
            "body": body,
            "errore": errore,
            "token": token,
            "testo": request.form.get("text", ""),
        }

    return render_template(template, esito=esito, **contesto)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/visible-it", methods=["GET", "POST"])
def visible_it():
    return _gestisci_invio("visible-it.html", localizzato=True)


@app.route("/visible-en", methods=["GET", "POST"])
def visible_en():
    # Stesso widget senza attributi data-cap-i18n-*: mostra le etichette
    # inglesi predefinite.
    return _gestisci_invio("visible-en.html", localizzato=False)


@app.route("/invisible", methods=["GET", "POST"])
def invisible():
    return _gestisci_invio("invisible.html")


SCENARI_ERRORI = {
    "ok": "Verifica normale",
    "riuso": "Riuso dello stesso token",
    "scaduto": "Token scaduto",
    "mancante": "Token assente",
    "contraffatto": "Token inventato",
    "secret": "Chiave segreta errata",
}

# Lo scenario "secret" fa bloccare per 250 ms l'IP di questo server presso il
# servizio captcha: un throttle qui evita di saturarlo se qualcuno clicca
# ripetutamente.
_ultimo_scenario_secret = {"ts": 0.0}


def _esegui_scenario(scenario, token, token_scaduto):
    """Forza deliberatamente uno dei casi della tabella risposte di siteverify.

    A differenza di _gestisci_invio, qui l'obiettivo non è verificare
    correttamente: è dimostrare un errore specifico.
    """
    if scenario == "riuso":
        # La prima verifica consuma il token; l'esito istruttivo è quello
        # della seconda.
        verifica_captcha(CAPJS_INTERNAL_URL, CAPJS_SITE_KEY, CAPJS_SECRET, token)
        return verifica_captcha(CAPJS_INTERNAL_URL, CAPJS_SITE_KEY, CAPJS_SECRET, token)

    if scenario == "scaduto":
        if not (CAPJS_SITE_KEY_SHORT_TTL and CAPJS_SECRET_SHORT_TTL):
            return (
                False,
                None,
                {},
                "Chiave a scadenza breve non configurata su questa istanza "
                "(richiede la versione aggiornata di demo-init).",
            )
        return verifica_captcha(
            CAPJS_INTERNAL_URL, CAPJS_SITE_KEY_SHORT_TTL, CAPJS_SECRET_SHORT_TTL, token_scaduto
        )

    if scenario == "mancante":
        return verifica_captcha(CAPJS_INTERNAL_URL, CAPJS_SITE_KEY, CAPJS_SECRET, "")

    if scenario == "contraffatto":
        return verifica_captcha(
            CAPJS_INTERNAL_URL, CAPJS_SITE_KEY, CAPJS_SECRET, "token-inventato:0000"
        )

    if scenario == "secret":
        adesso = time.monotonic()
        if adesso - _ultimo_scenario_secret["ts"] < 2:
            return (
                False,
                None,
                {},
                "Riprova fra qualche secondo: questo scenario è limitato per "
                "non far bloccare ripetutamente l'IP del server presso il "
                "servizio captcha.",
            )
        _ultimo_scenario_secret["ts"] = adesso
        return verifica_captcha(
            CAPJS_INTERNAL_URL, CAPJS_SITE_KEY, CAPJS_SECRET + "-non-valida", token or "qualsiasi-valore"
        )

    # "ok" e qualunque valore non riconosciuto.
    return verifica_captcha(CAPJS_INTERNAL_URL, CAPJS_SITE_KEY, CAPJS_SECRET, token)


@app.route("/errori", methods=["GET", "POST"])
def errori():
    esito = None

    if request.method == "POST" and DEMO_ERRORI_ENABLED:
        scenario = request.form.get("scenario", "ok")
        token = request.form.get(CAMPO_TOKEN)
        token_scaduto = request.form.get("capjs-token-scaduto-catturato")
        ok, status, body, errore = _esegui_scenario(scenario, token, token_scaduto)
        esito = {
            "ok": ok,
            "status": status,
            "body": body,
            "errore": errore,
            "scenario_label": SCENARI_ERRORI.get(scenario, scenario),
        }

    return render_template(
        "errori.html",
        esito=esito,
        site_key_short_ttl=CAPJS_SITE_KEY_SHORT_TTL,
    )


@app.route("/guida")
def guida():
    return render_template("guida.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
