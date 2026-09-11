FROM oven/bun:1.4.0-slim AS base
WORKDIR /usr/src/app

FROM base AS install
RUN mkdir -p /temp/dev
COPY package.json bun.lock /temp/dev/
RUN cd /temp/dev && bun install

FROM base AS prod
RUN mkdir -p /temp/prod
COPY package.json bun.lock /temp/prod/
RUN cd /temp/prod && bun install --production

FROM base AS prerelease
COPY --from=install /temp/dev/node_modules node_modules
COPY . .

# Vendorizza gli asset del widget (JS + WASM) nell'immagine: vedi il
# commento in scripts/vendor-assets.mjs sul perche' non basta scaricarli a
# runtime in src/assets.js.
FROM base AS assets
ARG WIDGET_VERSION=0.1.33
ARG WASM_VERSION=0.0.6
COPY scripts/vendor-assets.mjs scripts/vendor-assets.mjs
RUN mkdir -p /vendor && \
    WIDGET_VERSION=${WIDGET_VERSION} WASM_VERSION=${WASM_VERSION} \
    bun run scripts/vendor-assets.mjs /vendor

FROM base AS release
COPY --from=prod /temp/prod/node_modules node_modules
COPY --from=prerelease /usr/src/app .
COPY --from=assets /vendor vendor
WORKDIR /usr/src/app

EXPOSE 3000/tcp

USER bun

ENTRYPOINT [ "bun", "run", "./src/index.js" ]
