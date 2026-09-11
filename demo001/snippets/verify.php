<?php
/**
 * Verifica lato server di un token RERCaptcha.
 *
 * Non eseguito da questa demo (che è scritta in Python): la coerenza con il
 * contratto reale del servizio è garantita dai test in tests/test_snippets.py,
 * che controllano che parametri, nome del campo e path restino allineati
 * all'implementazione Python.
 */

/**
 * Verifica un token RERCaptcha interrogando il servizio.
 *
 * @param string $baseUrl URL del servizio raggiungibile DAL TUO SERVER
 *                         (non quello usato dal browser).
 * @param string $siteKey Chiave pubblica del sito.
 * @param string $secret  Chiave segreta. Non deve mai raggiungere il browser.
 * @param string $token   Valore del campo "capjs-token" arrivato con la form.
 * @param int    $timeout Secondi oltre i quali rinunciare.
 *
 * @return array{ok: bool, status: ?int, body: array, errore: ?string}
 */
function verifica_captcha(string $baseUrl, string $siteKey, string $secret, ?string $token, int $timeout = 5): array
{
    // Il token vuoto non va nemmeno inviato: il servizio risponderebbe 400.
    // Un token assente non significa necessariamente che l'utente non abbia
    // risolto il captcha: il widget svuota il campo da sé quando il token
    // scade, quindi questo caso capita anche a chi ha compilato la form
    // troppo lentamente.
    if (empty($token)) {
        return [
            'ok' => false,
            'status' => null,
            'body' => [],
            'errore' => 'Token del captcha assente. Se avevi già risolto il captcha, è probabile che sia scaduto: risolvilo di nuovo.',
        ];
    }

    $url = rtrim($baseUrl, '/') . "/{$siteKey}/siteverify";

    $ch = curl_init($url);
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => http_build_query([
            'secret' => $secret,
            'response' => $token,
        ]),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => $timeout,
    ]);

    $risposta = curl_exec($ch);
    $errno = curl_errno($ch);
    $errmsg = curl_error($ch);
    $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($risposta === false || $errno !== 0) {
        // Servizio non raggiungibile, DNS, TLS, timeout di connessione...
        // Da loggare: è un problema di infrastruttura, non dell'utente.
        return [
            'ok' => false,
            'status' => null,
            'body' => [],
            'errore' => "Servizio captcha non raggiungibile: {$errmsg}",
        ];
    }

    // ATTENZIONE: non basarti solo sullo status HTTP per decidere se leggere
    // il corpo. Il servizio risponde con {"error": "..."} anche sui codici
    // 4xx, e quel messaggio va letto, non scartato.
    $body = json_decode($risposta, true) ?? [];

    if ($status === 200 && ($body['success'] ?? false)) {
        return ['ok' => true, 'status' => $status, 'body' => $body, 'errore' => null];
    }

    return [
        'ok' => false,
        'status' => $status,
        'body' => $body,
        'errore' => messaggio_errore($status, $body['error'] ?? ''),
    ];
}

/**
 * Traduce la risposta del servizio in un messaggio comprensibile.
 *
 * Il servizio distingue i casi con la coppia (status HTTP, campo "error"):
 * lo stesso testo "Invalid site key or secret" arriva con 404 se la site key
 * è sconosciuta e con 403 se il secret è sbagliato.
 */
function messaggio_errore(?int $status, string $errore): string
{
    if ($status === 429) {
        return "Troppe richieste di verifica. Rispetta l'header Retry-After e non ritentare in loop.";
    }
    if ($status === 400) {
        return "Parametri mancanti nella richiesta di verifica: controlla di leggere il campo 'capjs-token' e di inviare 'secret' e 'response'.";
    }
    if ($status === 403 && $errore === 'Token expired') {
        return 'Il captcha è scaduto. Risolvilo di nuovo e reinvia la form.';
    }
    if ($status === 403) {
        return "Chiave segreta non valida. È un errore di configurazione del server, non dell'utente.";
    }
    if ($status === 404 && $errore === 'Token not found') {
        // Causa più frequente: il token era già stato verificato una volta.
        // I token sono monouso: un secondo controllo è indistinguibile da un
        // token inventato.
        return 'Captcha non valido o già utilizzato. I token sono monouso: verificane uno una sola volta.';
    }
    if ($status === 404) {
        return 'Site key sconosciuta: controlla la configurazione del server.';
    }

    return "Verifica del captcha non riuscita (HTTP {$status}): " . ($errore ?: 'errore sconosciuto');
}

// Esempio d'uso. Sostituisci i placeholder con i valori del tuo sito: la site
// key è pubblica, la secret key va letta dalla configurazione del server e
// non deve mai finire in un repository.
//
// $risultato = verifica_captcha(
//     'https://captcha.tuodominio.it',
//     'SITE_KEY_PUBBLICA',
//     'SECRET_KEY_PRIVATA',
//     $_POST['capjs-token'] ?? null
// );
//
// if ($risultato['ok']) {
//     // procedi con l'elaborazione della form
// } else {
//     // mostra $risultato['errore'] all'utente, logga $risultato['body']
// }
