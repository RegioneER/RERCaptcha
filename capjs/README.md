# CapJS Service

Il servizio `capjs` è il cuore del sistema RER Captcha. È una versione
vendorizzata (non un submodule) di [Cap.js](https://github.com/tiagozip/cap)
(`standalone@3.1.11`), con alcune modifiche locali per accessibilità e
sicurezza: aggiuntive rispetto all'origin, elencate in fondo a questo file.

## API Endpoints

### 1. Verifica Token

Verifica se un token inviato dal client è valido.

- **URL**: `/:site_key/siteverify`
- **Metodo**: `POST`
- **Body (JSON)**:
  - `secret`: la secret key del sito, ottenuta creando la site key dalla dashboard.
  - `response`: il token generato dal widget CapJS dopo la risoluzione della sfida.
- **Risposta**:
  ```json
  { "success": true | false, "error": "..." }
  ```

Le API di gestione (creazione/configurazione site key, API key, impostazioni)
sono sotto `/server/*` e richiedono un token di sessione o API key — vedi la
documentazione Swagger esposta dal servizio stesso (`/swagger`).

## Configurazione

Il servizio è configurato tramite variabili d'ambiente (vedi `compose.yml`
per i valori usati in questo repo):

- `ADMIN_KEY`: password dell'account admin della dashboard (obbligatoria).
- `REDIS_URL` / `VALKEY_URL`: connessione a Redis/Valkey, **obbligatoria**
  a partire da questa versione (lo storage non è più SQLite locale).
- `SERVER_PORT` / `SERVER_HOSTNAME`: porta/host di ascolto (default `3000` / `0.0.0.0`).
- `WIDGET_VERSION`, `WASM_VERSION`, `ENABLE_ASSETS_SERVER`: servono gli
  asset del widget/wasm direttamente da questo servizio invece che da una CDN.
- `CORS_ORIGIN`: origini consentite per le chiamate cross-origin del widget.
- `LOGIN_PAGE_ENABLED`: se `true`, la pagina di login è raggiungibile
  pubblicamente; altrimenti risponde 403 salvo passare per l'autologin.
- `VERIFY_HEADER` (`nome:valore`, modifica locale): se l'header in arrivo
  coincide, la dashboard fa autologin tramite il reverse proxy IAM
  regionale invece di richiedere l'ADMIN_KEY.

## Modifiche locali rispetto all'origin

Rispetto a [tiagozip/cap](https://github.com/tiagozip/cap), questo servizio
aggiunge:

- **Autologin via reverse proxy IAM** (`VERIFY_HEADER`, `LOGIN_PAGE_ENABLED`,
  `public/autologin.html`) — `src/index.js`, `src/auth.js`.
- **Security header HTTP globali** (`X-Content-Type-Options: nosniff`,
  `Content-Security-Policy: default-src 'self'`) su tutte le risposte,
  non solo sulle route admin — `src/index.js`.
- **Accessibilità WCAG**: aria-label sui controlli icona-only, heading
  semantici, focus-trap e ruoli ARIA sulle modali della dashboard,
  rispetto di `prefers-reduced-motion` — `public/`.
- **TTL configurabile per site key** (`expiresMS`/`tokenTTL`, separati dai
  valori fissi upstream) — `src/cap.js`, `src/server.js`, dashboard.

## Migrazione da versioni precedenti (storage SQLite)

Le versioni precedenti di questo servizio (fino a `standalone@2.0.18`)
usavano uno storage SQLite locale (`bun:sqlite`/`bun` SQL). Da questa
versione lo storage è Redis/Valkey e non c'è più supporto SQLite.

Per portare site key e API key esistenti su Redis, usa
`capjs/standalone/scripts/migrate-sqlite-to-redis.mjs`:

```sh
# 1. SEMPRE prima una prova, anche su una copia del file:
SQLITE_PATH=/path/to/db.sqlite REDIS_URL=redis://localhost:6379 \
  bun run capjs/standalone/scripts/migrate-sqlite-to-redis.mjs --dry-run

# 2. Solo dopo aver verificato l'output: ferma il vecchio capjs, avvia
#    valkey e il nuovo capjs, poi esegui per davvero (senza --dry-run)
#    puntando al file sqlite del vecchio deployment.
```

Lo script migra solo i dati durevoli (site key, API key); sessioni,
sfide e token di verifica in corso sono dati effimeri (TTL di minuti/ore)
e non vengono migrati — equivalente a quanto già succede a ogni riavvio
del servizio.

## Deployment

Il servizio è containerizzato tramite Docker (vedere `standalone/Dockerfile`)
e richiede un'istanza Redis/Valkey raggiungibile (vedi il servizio `valkey`
in `compose.yml`). In ambiente di sviluppo viene eseguito insieme a un
container che funge da reverse proxy per il traffico pubblico.

## Widget Client-side

Per integrare il widget nel frontend, è necessario caricare lo script
JavaScript fornito dal servizio (direttamente o tramite un proxy):

```html
<script src="http://localhost:3000/assets/widget.js" async defer></script>
```

_(Nota: l'URL esatto dipende da `ENABLE_ASSETS_SERVER` e dalla configurazione del proxy)_
