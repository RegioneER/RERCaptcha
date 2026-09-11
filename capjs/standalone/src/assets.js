import path from "node:path";
import { Elysia, file } from "elysia";

// Asset del widget (JS + WASM) vendorizzati nell'immagine a build time (vedi
// Dockerfile, stage "assets", e scripts/vendor-assets.mjs): il servizio non
// contatta mai cdn.jsdelivr.net a runtime. Per un ente pubblico quel
// traffico verso terze parti va autorizzato esplicitamente (vedi
// demo001/templates/guida.html), e in ambienti con egress ristretto
// (tipico di una rete OpenShift regionale) un fetch periodico sarebbe
// comunque inaffidabile. Per aggiornare gli asset: bump di
// WIDGET_VERSION/WASM_VERSION come build arg e rebuild dell'immagine.
const VENDOR_DIR =
  process.env.CAPJS_VENDOR_DIR || path.join(import.meta.dir, "..", "vendor");

export const assetsServer = new Elysia({
  prefix: "/assets",
  detail: { tags: ["Assets"] },
})
  .onBeforeHandle(({ set }) => {
    if (process.env.ENABLE_ASSETS_SERVER !== "true") {
      set.status = 404;
      return "Asset server is disabled. Set ENABLE_ASSETS_SERVER=true to enable it.";
    }
    set.headers["Cache-Control"] = "max-age=31536000, immutable";
  })
  .get("/widget.js", ({ set }) => {
    set.headers["Content-Type"] = "text/javascript";
    return file(path.join(VENDOR_DIR, "assets-widget.js"));
  })
  .get("/floating.js", ({ set }) => {
    set.headers["Content-Type"] = "text/javascript";
    return file(path.join(VENDOR_DIR, "assets-floating.js"));
  })
  .get("/cap_wasm_bg.wasm", ({ set }) => {
    set.headers["Content-Type"] = "application/wasm";
    return file(path.join(VENDOR_DIR, "assets-cap_wasm_bg.wasm"));
  })
  .get("/cap_wasm.js", ({ set }) => {
    set.headers["Content-Type"] = "text/javascript";
    return file(path.join(VENDOR_DIR, "assets-cap_wasm.js"));
  });
