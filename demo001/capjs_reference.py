"""Tabelle di riferimento di RERCaptcha: unica fonte per la guida.

Ogni valore qui è stato letto dal codice reale, non assunto:

- attributi, chiavi i18n, eventi, globali e custom property provengono dal
  bundle del widget servito da `/assets/widget.js`;
- le risposte di `siteverify` provengono da `capjs/standalone/src/siteverify.js`;
- i limiti di frequenza da `capjs/standalone/src/cap.js`.

Sono sole strutture dati, senza dipendenze: la guida le rende con una macro
Jinja e i test in `tests/test_snippets.py` verificano che ciò che la demo usa
sia effettivamente documentato qui.
"""

# Nome del campo hidden usato in tutta la demo. Va tenuto allineato a
# `snippets.verify.CAMPO_TOKEN` e ai partial: è ciò che verifica il test 2.
CAMPO_TOKEN = "capjs-token"


# --- Attributi di configurazione di <cap-widget> ---------------------------

DATA_ATTRS = [
    {
        "attributo": "data-cap-api-endpoint",
        "obbligatorio": True,
        "default": "—",
        "descrizione": (
            "URL base del servizio, comprensivo di site key. Deve terminare "
            "con una barra: il widget vi concatena <code>challenge</code> e "
            "<code>redeem</code>. Va usato l'URL raggiungibile dal browser."
        ),
    },
    {
        "attributo": "data-cap-hidden-field-name",
        "obbligatorio": False,
        "default": "cap-token",
        "descrizione": (
            "Nome del campo hidden che il widget crea al proprio interno e in "
            "cui scrive il token. Se lo ometti il campo si chiama "
            "<code>cap-token</code>: è il nome che dovrai leggere sul server."
        ),
    },
    {
        "attributo": "data-cap-worker-count",
        "obbligatorio": False,
        "default": "navigator.hardwareConcurrency, altrimenti 8",
        "descrizione": (
            "Numero di web worker impiegati per risolvere la sfida. Abbassarlo "
            "riduce l'uso di CPU sul dispositivo dell'utente ma allunga i tempi."
        ),
    },
]


# --- Chiavi di localizzazione: data-cap-i18n-<chiave> ----------------------
#
# `aria` distingue le chiavi che alimentano il nome accessibile del widget:
# sono le uniche fonti possibili, perché <label for> non si associa a un
# custom element in shadow DOM.

I18N_KEYS = [
    {
        "chiave": "initial-state",
        "default": "I'm a human",
        "aria": False,
        "quando": "Testo iniziale, prima che l'utente interagisca.",
    },
    {
        "chiave": "verifying-label",
        "default": "Verifying...",
        "aria": False,
        "quando": "Durante la risoluzione della sfida.",
    },
    {
        "chiave": "solved-label",
        "default": "You're a human",
        "aria": False,
        "quando": "A verifica completata.",
    },
    {
        "chiave": "error-label",
        "default": "Error. Try again.",
        "aria": False,
        "quando": "In caso di errore.",
    },
    {
        "chiave": "wasm-disabled",
        "default": "Enable WASM for significantly faster solving",
        "aria": False,
        "quando": "Se WebAssembly non è disponibile nel browser.",
    },
    {
        "chiave": "verify-aria-label",
        "default": "Click to verify you're a human",
        "aria": True,
        "quando": "Nome accessibile nello stato iniziale.",
    },
    {
        "chiave": "verifying-aria-label",
        "default": "Verifying you're a human, please wait",
        "aria": True,
        "quando": "Nome accessibile durante la verifica.",
    },
    {
        "chiave": "verified-aria-label",
        "default": "We have verified you're a human, you may now continue",
        "aria": True,
        "quando": "Nome accessibile a verifica completata.",
    },
    {
        "chiave": "error-aria-label",
        "default": "An error occurred, please try again",
        "aria": True,
        "quando": "Nome accessibile in caso di errore.",
    },
]


# --- Eventi -----------------------------------------------------------------
#
# Tutti sono CustomEvent con bubbles e composed a true, quindi restano
# intercettabili anche fuori dallo shadow DOM, per esempio sul document.

EVENTS = [
    {
        "evento": "solve",
        "attributo": "onsolve",
        "detail": "{ token }",
        "quando": (
            "La sfida è stata risolta e il token è disponibile. È l'evento su "
            "cui abilitare il pulsante di invio."
        ),
    },
    {
        "evento": "progress",
        "attributo": "onprogress",
        "detail": "{ progress }",
        "quando": "Avanzamento della risoluzione, da 0 a 100.",
    },
    {
        "evento": "reset",
        "attributo": "onreset",
        "detail": "—",
        "quando": (
            "Il widget è tornato allo stato iniziale e ha svuotato il campo "
            "hidden. Accade anche da sé alla scadenza del token: è l'evento su "
            "cui ri-disabilitare il pulsante di invio."
        ),
    },
    {
        "evento": "error",
        "attributo": "onerror",
        "detail": "{ message, isCap }",
        "quando": "La risoluzione è fallita.",
    },
]

# Gli attributi onsolve/onprogress/onreset/onerror non accettano espressioni
# JavaScript come gli handler HTML classici: il valore viene cercato fra le
# funzioni globali, quindi va indicato il solo nome della funzione.
METHODS = [
    {
        "nome": "solve()",
        "descrizione": "Avvia la risoluzione. Restituisce una Promise.",
    },
    {
        "nome": "reset()",
        "descrizione": "Riporta il widget allo stato iniziale e svuota il token.",
    },
    {
        "nome": "token",
        "descrizione": "Proprietà di sola lettura con il token corrente, o null.",
    },
]


# --- Variabili globali di configurazione ----------------------------------

GLOBALS = [
    {
        "nome": "window.CAP_CUSTOM_WASM_URL",
        "descrizione": (
            "URL del modulo WebAssembly. <strong>Va impostata prima di caricare "
            "widget.js</strong>: il widget legge questa variabile al momento del "
            "caricamento e, se la trova vuota, inserisce nella pagina dei "
            "<code>&lt;link rel=\"prefetch\"&gt;</code> verso "
            "<code>cdn.jsdelivr.net</code> e scarica il WASM da quella CDN."
        ),
    },
    {
        "nome": "window.CAP_CSS_NONCE",
        "descrizione": (
            "Nonce applicato al tag <code>&lt;style&gt;</code> che il widget "
            "inietta nel proprio shadow DOM. Serve se la tua CSP dichiara "
            "<code>style-src</code>, e permette di non ricorrere a "
            "<code>'unsafe-inline'</code>."
        ),
    },
    {
        "nome": "window.CAP_CUSTOM_FETCH",
        "descrizione": (
            "Funzione alternativa per le chiamate di rete, in luogo di "
            "<code>data-cap-api-endpoint</code>."
        ),
    },
    {
        "nome": "window.CAP_DONT_SKIP_REDEFINE",
        "descrizione": (
            "Forza la ridefinizione del custom element se risultasse già "
            "registrato. Utile solo in caso di doppio caricamento dello script."
        ),
    },
]


# --- Risposte di POST {base}/{siteKey}/siteverify -------------------------

SITEVERIFY_RESPONSES = [
    {
        "status": 200,
        "body": '{"success": true}',
        "causa": "Captcha valido. Il token viene cancellato: è monouso.",
        "cosa_fare": "Procedi con l'elaborazione della form.",
    },
    {
        "status": 400,
        "body": '{"error": "Missing required parameters"}',
        "causa": "Manca uno fra site key, secret e response.",
        "cosa_fare": (
            "Errore di programmazione: controlla di leggere il campo giusto "
            "della form. Non ritentare."
        ),
    },
    {
        "status": 404,
        "body": '{"error": "Invalid site key or secret"}',
        "causa": "La site key non esiste.",
        "cosa_fare": "Errore di configurazione: verifica la chiave. Non ritentare.",
    },
    {
        "status": 403,
        "body": '{"error": "Invalid site key or secret"}',
        "causa": (
            "La chiave segreta è sbagliata. Il servizio blocca per 250 ms l'IP "
            "che ha chiamato, cioè il tuo server."
        ),
        "cosa_fare": (
            "Errore di configurazione, da segnalare subito: mentre dura, le "
            "verifiche legittime possono ricevere 429."
        ),
    },
    {
        "status": 404,
        "body": '{"error": "Token not found"}',
        "causa": (
            "Il token non esiste, oppure era già stato verificato: essendo "
            "monouso, i due casi sono indistinguibili."
        ),
        "cosa_fare": (
            "Rifiuta l'invio e ri-mostra il captcha. Controlla di non "
            "verificare due volte lo stesso token."
        ),
    },
    {
        "status": 403,
        "body": '{"error": "Token expired"}',
        "causa": "Il token è più vecchio del tokenTTL configurato per la chiave.",
        "cosa_fare": (
            "Chiedi all'utente di risolvere di nuovo il captcha. Non è un suo "
            "errore: è una form rimasta aperta troppo a lungo."
        ),
    },
    {
        "status": 429,
        "body": '{"error": "You were temporarily ..."}',
        "causa": (
            "Troppe richieste dallo stesso IP, in genere dopo una chiamata con "
            "secret errato. La risposta porta l'header Retry-After."
        ),
        "cosa_fare": "Rispetta Retry-After. Non ritentare in loop.",
    },
]


# --- Personalizzazione grafica -------------------------------------------
#
# Il widget vive in shadow DOM: i normali selettori CSS non lo raggiungono,
# mentre le custom property e ::part() sì.

CSS_VARS = [
    {"nome": "--cap-background", "default": "#fdfdfd"},
    {"nome": "--cap-border-color", "default": "#dddddd8f"},
    {"nome": "--cap-border-radius", "default": "14px"},
    {"nome": "--cap-checkbox-background", "default": "#fafafa91"},
    {"nome": "--cap-checkbox-border", "default": "1px solid #aaaaaad1"},
    {"nome": "--cap-checkbox-border-radius", "default": "6px"},
    {"nome": "--cap-checkbox-margin", "default": "2px"},
    {"nome": "--cap-checkbox-size", "default": "25px"},
    {"nome": "--cap-checkmark", "default": "SVG inline (spunta verde)"},
    {"nome": "--cap-color", "default": "#212121"},
    {"nome": "--cap-error-cross", "default": "SVG inline (croce rossa)"},
    {"nome": "--cap-font", "default": "font di sistema"},
    {"nome": "--cap-gap", "default": "15px"},
    {"nome": "--cap-spinner-background-color", "default": "#eee"},
    {"nome": "--cap-spinner-color", "default": "#000"},
    {"nome": "--cap-spinner-thickness", "default": "3"},
    {"nome": "--cap-widget-height", "default": "58px"},
    {"nome": "--cap-widget-padding", "default": "14px"},
    {"nome": "--cap-widget-width", "default": "230px"},
]

CSS_PARTS = [
    {"nome": "checkbox", "descrizione": "La casella di spunta."},
    {"nome": "label", "descrizione": "Il testo di stato accanto alla casella."},
    {"nome": "attribution", "descrizione": 'La dicitura "Secured by Cap".'},
]


# --- Limiti di frequenza --------------------------------------------------

RATE_LIMITS = [
    {
        "ambito": "POST /{siteKey}/challenge e /{siteKey}/redeem",
        "limite": "45 richieste ogni 5 secondi per IP",
        "note": (
            "Sono chiamate fatte dal browser dell'utente. Dietro reverse proxy "
            "il servizio deve avere <code>RATELIMIT_IP_HEADER</code> "
            "configurato, altrimenti il conteggio è inefficace."
        ),
    },
    {
        "ambito": "POST /{siteKey}/siteverify",
        "limite": "blocco di 250 ms dopo una chiamata con secret errato",
        "note": (
            "Il blocco vale per l'IP chiamante, cioè il tuo server. Le "
            "richieste successive nella finestra ricevono 429 con Retry-After."
        ),
    },
]
