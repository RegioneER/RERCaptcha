import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";

// login.html e autologin.html (le uniche pagine di bootstrap servite
// direttamente da questo processo, non bundle esterni come il resto della
// dashboard) usano <script>/<style> inline. La CSP globale in src/index.js
// e' "default-src 'self'" senza 'unsafe-inline': senza questi hash il
// browser blocca silenziosamente quell'inline e login/autologin restano
// bloccati sullo spinner (nessun redirect, nessun errore lato server).
//
// Calcoliamo gli hash qui invece di scriverli a mano: se questi due file
// cambiano (es. refresh da upstream cap.js), gli hash si aggiornano da soli
// al prossimo avvio, senza bisogno di risincronizzare stringhe sha256- a
// mano nella CSP.
const INLINE_SOURCE_FILES = ["login.html", "autologin.html"].map((name) =>
  path.join(import.meta.dir, "..", "public", name),
);

function extractInlineHashes(files) {
  const scriptHashes = new Set();
  const styleHashes = new Set();
  const blockRe = /<(script|style)(?:\s[^>]*)?>([\s\S]*?)<\/\1>/g;

  for (const filePath of files) {
    const html = readFileSync(filePath, "utf-8");
    let match;
    while ((match = blockRe.exec(html))) {
      const [, tag, content] = match;
      const hash = `'sha256-${createHash("sha256").update(content).digest("base64")}'`;
      (tag === "script" ? scriptHashes : styleHashes).add(hash);
    }
  }

  return { scriptHashes: [...scriptHashes], styleHashes: [...styleHashes] };
}

const { scriptHashes, styleHashes } = extractInlineHashes(INLINE_SOURCE_FILES);

export const CONTENT_SECURITY_POLICY = [
  "default-src 'self'",
  ["script-src", "'self'", ...scriptHashes].join(" "),
  ["style-src", "'self'", ...styleHashes].join(" "),
].join("; ");
