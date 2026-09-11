# Licenze di terze parti

RER Captcha è distribuito sotto licenza Apache-2.0 (vedi [LICENSE](LICENSE))
e include o dipende dalle librerie open source elencate qui sotto. Per la
parte JavaScript sono elencate solo le dipendenze dirette dichiarate nei
rispettivi `package.json` (non l'intero albero transitivo in
`node_modules`); per la parte Python le versioni sono quelle pinnate in
`demo001/constraints.txt`.

## Servizio `capjs` ([capjs/standalone](capjs/standalone))

Il servizio è basato su **CapJS**, il progetto open source di riferimento:

- **[@cap.js/server](https://github.com/tiagozip/cap)** — Apache-2.0 —
  Copyright ©2025 - present tiago

Dipendenze dirette del servizio (`capjs/standalone/package.json`):

| Pacchetto | Licenza | Autore/progetto |
| --- | --- | --- |
| [elysia](https://github.com/elysiajs/elysia) | MIT | saltyAom |
| [@elysiajs/cors](https://github.com/elysiajs/elysia-cors) | MIT | saltyAom |
| [@elysiajs/static](https://github.com/elysiajs/elysia-static) | MIT | saltyAom |
| [@elysiajs/swagger](https://github.com/elysiajs/elysia-swagger) | MIT | saltyAom |
| [elysia-rate-limit](https://github.com/rayriffy/elysia-rate-limit) | MIT | rayriffy |

Runtime di esecuzione (immagine base `oven/bun:1` in
[capjs/standalone/Dockerfile](capjs/standalone/Dockerfile)):

- **[Bun](https://github.com/oven-sh/bun)** — MIT — Oven

## Applicazione demo `demo001`

Dipendenze Python (`demo001/constraints.txt`):

| Pacchetto | Licenza |
| --- | --- |
| [Flask](https://github.com/pallets/flask) | BSD-3-Clause |
| [Werkzeug](https://github.com/pallets/werkzeug) | BSD-3-Clause |
| [Jinja2](https://github.com/pallets/jinja) | BSD-3-Clause |
| [MarkupSafe](https://github.com/pallets/markupsafe) | BSD-3-Clause |
| [itsdangerous](https://github.com/pallets/itsdangerous) | BSD-3-Clause |
| [click](https://github.com/pallets/click) | BSD-3-Clause |
| [blinker](https://github.com/pallets-eco/blinker) | MIT |
| [gunicorn](https://github.com/benoitc/gunicorn) | MIT |
| [requests](https://github.com/psf/requests) | Apache-2.0 |
| [charset-normalizer](https://github.com/jawah/charset_normalizer) | MIT |
| [idna](https://github.com/kjd/idna) | BSD-3-Clause |
| [urllib3](https://github.com/urllib3/urllib3) | MIT |
| [certifi](https://github.com/certifi/python-certifi) | MPL-2.0 |
| [packaging](https://github.com/pypa/packaging) | Apache-2.0 OR BSD-2-Clause |
| [Pygments](https://pygments.org/) | BSD-2-Clause |

Runtime di esecuzione (immagine base `python:3.11-slim` in
[demo001/Dockerfile](demo001/Dockerfile)):

- **[Python](https://www.python.org/)** — PSF License

Asset frontend vendorizzati in `demo001/static/`:

- **[Bootstrap](https://getbootstrap.com/)** 5.3.8 — MIT — Copyright
  2011-2025 The Bootstrap Authors (`demo001/static/bootstrap.min.css`)
- `demo001/static/pygments.css` non è codice di terzi a sé stante: è il
  foglio di stile generato una tantum dal tema "default" di Pygments (vedi
  Pygments sopra) e versionato per evitare di rigenerarlo a runtime.
