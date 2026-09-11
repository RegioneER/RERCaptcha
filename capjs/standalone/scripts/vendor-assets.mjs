#!/usr/bin/env bun
// Scarica gli asset del widget CapJS (JS + WASM) da jsdelivr e li scrive come
// file statici, nella forma servita da src/assets.js.
//
// Eseguito a build time dell'immagine Docker (vedi Dockerfile, stage
// "assets"). Il servizio capjs non fa mai fetch di questi file a runtime:
// in produzione l'egress del pod verso cdn.jsdelivr.net puo' non esserci
// (rete OpenShift ristretta), quindi la versione servita e' sempre e solo
// quella vendorizzata qui, pinnata da WIDGET_VERSION/WASM_VERSION.
// Per aggiornarla: bump delle versioni e rebuild dell'immagine.
//
// Uso:
//   WIDGET_VERSION=0.1.33 WASM_VERSION=0.0.6 \
//     bun run scripts/vendor-assets.mjs <outDir>

const CACHE_HOST = process.env.CACHE_HOST || "https://cdn.jsdelivr.net";
const WIDGET_VERSION = process.env.WIDGET_VERSION;
const WASM_VERSION = process.env.WASM_VERSION;
const outDir = process.argv[2];

if (!WIDGET_VERSION || !WASM_VERSION || !outDir) {
  console.error(
    "Usage: WIDGET_VERSION=... WASM_VERSION=... bun run vendor-assets.mjs <outDir>",
  );
  process.exit(1);
}

if (WIDGET_VERSION === "latest" || WASM_VERSION === "latest") {
  console.warn(
    "using 'latest' version for vendored assets is not recommended for production!\n   pin WIDGET_VERSION and WASM_VERSION to a fixed release instead.",
  );
}

// Il widget disegna il link "Secured by Cap" nel proprio shadow DOM tramite
// questa regola CSS. E' richiesto su tutti i siti RER che integrano il
// widget, quindi va nascosto una volta sola qui nel bundle vendorizzato
// invece che nel CSS di ogni sito integratore. Se un aggiornamento di
// WIDGET_VERSION cambia questo markup, il build fallisce rumorosamente
// invece di far ricomparire il link in silenzio.
const ATTRIBUTION_CSS_MARKER = ".captcha .credits{";

function hideAttributionLink(widgetSource) {
  if (!widgetSource.includes(ATTRIBUTION_CSS_MARKER)) {
    throw new Error(
      `marker CSS "${ATTRIBUTION_CSS_MARKER}" non trovato nel widget vendorizzato: ` +
        "il markup del link di attribuzione e' cambiato in questa WIDGET_VERSION, aggiorna questo script.",
    );
  }
  return widgetSource.replace(
    ATTRIBUTION_CSS_MARKER,
    `${ATTRIBUTION_CSS_MARKER}display:none;`,
  );
}

const files = [
  [`${CACHE_HOST}/npm/@cap.js/widget@${WIDGET_VERSION}`, "assets-widget.js"],
  [
    `${CACHE_HOST}/npm/@cap.js/widget@${WIDGET_VERSION}/cap-floating.min.js`,
    "assets-floating.js",
  ],
  [
    `${CACHE_HOST}/npm/@cap.js/wasm@${WASM_VERSION}/browser/cap_wasm_bg.wasm`,
    "assets-cap_wasm_bg.wasm",
  ],
  [
    `${CACHE_HOST}/npm/@cap.js/wasm@${WASM_VERSION}/browser/cap_wasm.min.js`,
    "assets-cap_wasm.js",
  ],
];

for (const [url, name] of files) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url} -> HTTP ${res.status}`);
  const body =
    name === "assets-widget.js"
      ? hideAttributionLink(await res.text())
      : await res.arrayBuffer();
  await Bun.write(`${outDir}/${name}`, body);
  console.log(`  ${name} <- ${url}`);
}

console.log(
  `vendored capjs assets (widget@${WIDGET_VERSION}, wasm@${WASM_VERSION}) into ${outDir}`,
);
