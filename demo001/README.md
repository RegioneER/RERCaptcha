# Demo 001 — RERCaptcha in Flask

Applicazione Flask che mostra RERCaptcha (basato su CapJS) integrato in form
reali, e include la guida completa per chi deve integrarlo su un altro sito.

## Avvio in locale

```bash
docker compose up -d capjs demo-init
docker compose up -d demo001
```

Le chiavi (`SITE_KEY`/`SECRET_KEY`) vengono generate al primo avvio da
`demo-init` e scritte in `shared/keys.json`: `demo001` le legge da lì in
automatico, senza bisogno di modificare `compose.yml`.

Per un deployment reale, valorizza invece le variabili d'ambiente `SITE_KEY`,
`SECRET_KEY`, `CAPJS_INTERNAL_URL` (URL del servizio raggiungibile dal
server) e `CAPJS_PUBLIC_URL` (URL raggiungibile dal browser).

## Pagine

- `/` — indice
- `/visible-it` — widget visibile, etichette in italiano
- `/visible-en` — lo stesso widget senza localizzazione
- `/invisible` — captcha risolto programmaticamente
- `/errori` — scenari di fallimento generati dal vivo (token riusato, token
  scaduto, chiave errata...). Disattivabile con `DEMO_ERRORI_ENABLED=false`.
- `/guida` — **la guida di integrazione**: client, server (Python/PHP/Java),
  CSP, risposte di `siteverify`, accessibilità, problemi frequenti.

## Test

```bash
pip install -r requirements.txt -c constraints.txt pytest
pytest
```

Verificano che gli esempi mostrati nella guida restino coerenti con il
contratto reale del servizio (nomi dei campi, ordine di caricamento degli
script, attributi documentati). Non richiedono un servizio capjs
raggiungibile.

## Struttura

- `app.py` — route, verifica del captcha, intestazioni di sicurezza
- `snippets/` — gli esempi di verifica server-side mostrati in `/guida`.
  `verify.py` non è solo un esempio: è il modulo che `app.py` importa ed
  esegue davvero.
- `capjs_reference.py` — le tabelle (attributi, eventi, risposte...) mostrate
  in `/guida`, in un unico posto
- `templates/partials/` — il markup del widget, condiviso fra le pagine demo
  (dove viene reso dal vivo) e la guida (dove viene mostrato come esempio)
- `tests/` — i test di coerenza descritti sopra
