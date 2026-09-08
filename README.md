# RER Captcha

RER Captcha è una soluzione di protezione captcha basata sul framework open-source **CapJS**. Questo repository contiene il servizio core e un'applicazione di esempio per facilitare l'integrazione.

## Architettura

Il progetto è composto da due componenti principali:

1.  **[capjs](capjs/README.md)**: Il servizio core che genera e verifica i captcha.
2.  **[demo001](demo001/README.md)**: Un'applicazione web Python/Flask che mostra come integrare CapJS in form reali e include la guida completa di integrazione (`/guida`).

I servizi sono orchestrati tramite Docker Compose per semplificare lo sviluppo e il deployment locale. Il repository include anche `demo`, un prototipo più semplice mantenuto come riferimento minimale.

## Guida alla Configurazione Rapida

Segui questi passaggi per avviare il sistema e testare la demo.

### 1. Requisiti

- Docker
- Docker Compose

### 2. Inizializzazione delle Chiavi

CapJS richiede una coppia di chiavi (`SITE_KEY` e `SECRET_KEY`) per funzionare. Queste vengono generate automaticamente al primo avvio.

```bash
# Avvia il core e il tool di inizializzazione
docker compose up -d capjs demo-init
```

Attendi qualche secondo, quindi recupera le chiavi generate:

```bash
cat shared/keys.json
```

L'output sarà simile a questo:

```json
{
  "siteKey": "xxxxxxxxxx",
  "secretKey": "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy",
  "siteKeyShortTTL": "zzzzzzzzzz",
  "secretKeyShortTTL": "wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww"
}
```

(Le due chiavi `*ShortTTL` servono solo alla pagina `/errori` di demo001 per
dimostrare la scadenza di un token; non sono necessarie in un'installazione
reale.)

### 3. Avvio della Demo

`demo001` legge automaticamente le chiavi da `shared/keys.json` quando le
variabili `SITE_KEY`/`SECRET_KEY` non sono valorizzate: non serve modificare
`compose.yml` per l'uso in locale.

```bash
docker compose up -d demo001
```

Per un deployment reale, valorizza invece in `compose.yml` (o in un file
`.env`) le variabili d'ambiente del servizio `demo001`:

```yaml
services:
  demo001:
    environment:
      SITE_KEY: "LA_TUA_SITE_KEY"
      SECRET_KEY: "LA_TUA_SECRET_KEY"
```

### 4. Accesso

Visita `http://localhost:5001` per vedere il captcha in azione, oppure
direttamente `http://localhost:5001/guida` per la guida completa di
integrazione.

## Documentazione Componenti

- [Documentazione Servizio CapJS](capjs/README.md)
- [Documentazione Demo Flask](demo001/README.md)

## Crediti e Licenza

RER Captcha si basa su [CapJS](https://github.com/tiagozip/cap) distribuito sotto licenza **Apache-2.0**.  Copyright ©2025 - present tiago.
