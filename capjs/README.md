# CapJS Service

Il servizio `capjs` è il cuore del sistema RER Captcha. Gestisce la generazione delle sfide captcha e la verifica dei token risolti.

Per l'integrazione lato sito (client e server), vedi la guida completa
servita dalla route `/guida` di [demo001](../demo001/README.md): qui sotto
solo il contratto essenziale e la configurazione del servizio.

## API Endpoints

### 1. Genera una sfida

- **URL**: `/:site_key/challenge`
- **Metodo**: `POST`
- **Risposta**: `{ "challenge": {...}, "token": "...", "expires": ... }`

### 2. Riscatta la soluzione

- **URL**: `/:site_key/redeem`
- **Metodo**: `POST`
- **Body**: `{ "token": "...", "solutions": [...] }`
- **Risposta**: `{ "success": true, "token": "...", "expires": ... }`

### 3. Verifica Token

Verifica se un token risolto dal client è valido. Va chiamato **dal server**,
mai dal browser: richiede la chiave segreta.

- **URL**: `/:site_key/siteverify`
- **Metodo**: `POST`
- **Parametri** (form-encoded o JSON):
  - `secret`: la `SECRET_KEY` del sito.
  - `response`: il token generato dal widget CapJS.
- **Risposta** (solo questi due campi, nessun altro):
  ```json
  { "success": true }
  ```
  Sugli errori il servizio risponde con status 4xx/429 e un corpo
  `{ "error": "..." }` — non con `success: false`. Non ci sono
  `challenge_ts`, `hostname` o `error-codes`: chi porta configurazioni da un
  altro servizio di captcha deve tenerne conto.

### 4. Asset del widget

Serviti da `/assets/` quando `ENABLE_ASSETS_SERVER=true`:
`widget.js`, `floating.js`, `cap_wasm.js`, `cap_wasm_bg.wasm`.

## Configurazione

Variabili d'ambiente principali:

- `SERVER_PORT`: porta su cui il servizio ascolta (default: `3000`).
- `SERVER_HOSTNAME`: interfaccia di ascolto (default: `0.0.0.0`).
- `ADMIN_KEY`: **obbligatoria**, almeno 30 caratteri. In produzione va
  spostata su un secret/vault, non lasciata nel compose file.
- `DATA_PATH`: directory dati (default: `./.data`).
- `CORS_ORIGIN`: origini ammesse per le chiamate dal browser
  (`challenge`/`redeem`/`siteverify`/asset), separate da virgola.
- `ENABLE_ASSETS_SERVER`: `true` per servire `/assets/*`.
- `WIDGET_VERSION` / `WASM_VERSION`: versioni da vendorizzare; da pinnare in
  produzione (il default `latest` genera un avviso).
- `LOGIN_PAGE_ENABLED`: `true` per mostrare la pagina di login su `/`.

## Deployment

Il servizio è containerizzato tramite Docker: vedere
`standalone/Dockerfile` per i dettagli della build (è quello usato da
`compose.yml`; il `Dockerfile` legacy nella directory `capjs/` non è più in
uso).
