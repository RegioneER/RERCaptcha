#!/usr/bin/env bun
// Migra le site key e le API key da un vecchio db.sqlite (cap.js < 3,
// storage bun:sqlite/bun SQL) al nuovo storage Redis/Valkey di cap.js v3.
//
// NON migra sessions/challenges/tokens: sono dati effimeri con TTL di
// minuti/ore, persi in qualunque restart del servizio (comportamento
// equivalente e gia' accettato oggi da un semplice riavvio di capjs).
//
// Uso:
//   SQLITE_PATH=/path/to/db.sqlite REDIS_URL=redis://localhost:6379 \
//     bun run scripts/migrate-sqlite-to-redis.mjs [--dry-run]
//
// Esegui SEMPRE prima con --dry-run (anche su una copia del file sqlite),
// verifica l'output, e solo dopo lancialo per davvero contro l'ambiente di
// produzione — dopo aver fermato il vecchio capjs, prima di avviare quello
// nuovo. Anche in --dry-run serve un Redis raggiungibile: viene usato in
// lettura per capire quali chiavi esistono gia' (nessuna scrittura avviene).
//
// Chiavi durevoli migrate 1:1:
//   keys.secretHash -> key:<siteKey> "secretHash" (copiato verbatim: e' un
//     hash Bun.password/argon2, riconosciuto e verificato dal path "legacy"
//     di verifySecret() in src/secret-hash.js, aggiornato al volo al primo
//     /siteverify riuscito)
//   api_keys.tokenHash -> apikey:<id> "tokenHash" (copiato verbatim, formato
//     invariato tra le due versioni)
// Campo nuovo generato ex novo (non esisteva prima di v2.2.0/v3):
//   key:<siteKey> "jwtSecret" (firma i JWT di sfida, capjs-core)

import { randomBytes } from "node:crypto";
import { Database } from "bun:sqlite";
import { db } from "../src/db.js";

const dryRun = process.argv.includes("--dry-run");
const sqlitePath = process.env.SQLITE_PATH;

if (!sqlitePath) {
  console.error("Imposta SQLITE_PATH al percorso del db.sqlite da migrare.");
  process.exit(1);
}

const sqlite = new Database(sqlitePath, { readonly: true });

function tableExists(name) {
  return !!sqlite
    .query("SELECT name FROM sqlite_master WHERE type='table' AND name = ?")
    .get(name);
}

async function migrateKeys() {
  if (!tableExists("keys")) {
    console.log("Nessuna tabella 'keys' nel db sqlite, salto.");
    return { migrated: 0, skipped: 0 };
  }

  const rows = sqlite.query("SELECT * FROM keys").all();
  let migrated = 0;
  let skipped = 0;

  for (const row of rows) {
    const siteKey = row.siteKey;

    if (await db.exists(`key:${siteKey}`)) {
      console.log(`- ${siteKey} (${row.name}): gia' presente su Redis, salto`);
      skipped++;
      continue;
    }

    let oldConfig = {};
    try {
      oldConfig = JSON.parse(row.config || "{}");
    } catch {
      console.warn(`  ! ${siteKey}: config non parsabile, uso i default`);
    }

    // saltSize non e' piu' configurabile lato server (sempre 32): non lo
    // riportiamo. Gli altri flag opzionali (rsw, instrumentation, cors,
    // rate limit...) non esistevano ancora nella versione precedente.
    const config = {
      difficulty: oldConfig.difficulty ?? 4,
      challengeCount: oldConfig.challengeCount ?? 80,
      expiresMS: oldConfig.expiresMS ?? 60_000,
      tokenTTL: oldConfig.tokenTTL ?? 120_000,
    };

    const jwtSecret = randomBytes(32).toString("base64url");

    console.log(
      `${dryRun ? "[dry-run] " : ""}+ ${siteKey} (${row.name}): secretHash copiato, jwtSecret generato`,
    );

    if (!dryRun) {
      await db.hmset(`key:${siteKey}`, [
        "name",
        row.name,
        "secretHash",
        row.secretHash,
        "jwtSecret",
        jwtSecret,
        "config",
        JSON.stringify(config),
        "created",
        String(row.created),
      ]);
      await db.sadd("keys", siteKey);
    }
    migrated++;
  }

  return { migrated, skipped };
}

async function migrateApiKeys() {
  if (!tableExists("api_keys")) {
    console.log("Nessuna tabella 'api_keys' nel db sqlite, salto.");
    return { migrated: 0, skipped: 0 };
  }

  const rows = sqlite.query("SELECT * FROM api_keys").all();
  let migrated = 0;
  let skipped = 0;

  for (const row of rows) {
    if (await db.exists(`apikey:${row.id}`)) {
      console.log(`- apikey ${row.id} (${row.name}): gia' presente su Redis, salto`);
      skipped++;
      continue;
    }

    console.log(`${dryRun ? "[dry-run] " : ""}+ apikey ${row.id} (${row.name})`);

    if (!dryRun) {
      await db.hmset(`apikey:${row.id}`, [
        "name",
        row.name,
        "tokenHash",
        row.tokenHash,
        "created",
        String(row.created),
      ]);
      await db.sadd("apikeys", row.id);
    }
    migrated++;
  }

  return { migrated, skipped };
}

console.log(
  `Migrazione da ${sqlitePath}${dryRun ? " (dry-run: nessuna scrittura su Redis)" : ""}`,
);

const keysResult = await migrateKeys();
const apiKeysResult = await migrateApiKeys();

console.log("\nRiepilogo:");
console.log(`  site key: ${keysResult.migrated} migrate, ${keysResult.skipped} gia' presenti`);
console.log(`  API key:  ${apiKeysResult.migrated} migrate, ${apiKeysResult.skipped} gia' presenti`);
console.log(
  "\nNota: sessions/challenges/tokens non sono stati migrati (dati effimeri, TTL minuti/ore).",
);

sqlite.close();
process.exit(0);
