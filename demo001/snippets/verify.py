"""Verifica lato server di un token RERCaptcha.

Questo file è contemporaneamente l'esempio mostrato nella guida (/guida#server)
e il modulo che la demo importa ed esegue: se l'esempio si rompe, si rompe la
demo. Per questo deve restare semplice e senza dipendenze dal framework web.

Se l'applicazione ha bisogno di logica aggiuntiva (retry, metriche, cache),
quella va scritta FUORI da qui: altrimenti l'esempio si gonfia e smette di
essere copiabile.

Dipendenze: solo `requests`.
"""

import requests

# Il nome del campo hidden in cui il widget scrive il token.
# Deve combaciare con `data-cap-hidden-field-name` nell'HTML.
# Attenzione: se ometti quell'attributo, il default del widget è "cap-token".
CAMPO_TOKEN = "capjs-token"


def verifica_captcha(base_url, site_key, secret, token, timeout=5):
    """Verifica un token RERCaptcha interrogando il servizio.

    Argomenti:
        base_url: URL base del servizio raggiungibile DAL TUO SERVER
                  (es. "http://capjs:3000" in rete interna).
                  Non è l'URL usato dal browser.
        site_key: la chiave pubblica del sito.
        secret:   la chiave segreta. Non deve mai raggiungere il browser.
        token:    il valore del campo `capjs-token` arrivato con la form.
        timeout:  secondi oltre i quali rinunciare.

    Ritorna la tupla (ok, status, body, errore):
        ok:     True solo se il captcha è valido.
        status: codice HTTP della risposta, oppure None se il servizio
                non è stato raggiunto.
        body:   il JSON di risposta come dict (vuoto se non decodificabile).
        errore: messaggio in italiano se ok è False, altrimenti None.
    """
    # Il token vuoto non va nemmeno inviato: il servizio risponderebbe 400.
    # Attenzione: un token assente non significa necessariamente che l'utente
    # non abbia risolto il captcha. Il widget svuota il campo da sé quando il
    # token scade (vedi /guida#token), quindi questo caso capita anche a
    # utenti legittimi che hanno compilato la form troppo lentamente.
    if not token:
        return False, None, {}, (
            "Token del captcha assente. Se avevi già risolto il captcha, "
            "è probabile che sia scaduto: risolvilo di nuovo."
        )

    url = f"{base_url}/{site_key}/siteverify"

    try:
        risposta = requests.post(
            url,
            data={"secret": secret, "response": token},
            timeout=timeout,
        )
    except requests.exceptions.RequestException as exc:
        # Servizio non raggiungibile, DNS, TLS, timeout di connessione...
        # Da loggare: è un problema di infrastruttura, non dell'utente.
        return False, None, {}, f"Servizio captcha non raggiungibile: {exc}"

    # ATTENZIONE: non usare `if risposta:` — equivale a `risposta.ok` ed è
    # falso per ogni 4xx, quindi butterebbe via proprio le risposte di errore
    # che spiegano cosa è andato storto.
    try:
        body = risposta.json()
    except ValueError:
        body = {}

    if risposta.status_code == 200 and body.get("success"):
        return True, risposta.status_code, body, None

    # Sugli errori il servizio risponde con {"error": "..."} e NON con
    # {"success": false}.
    return (
        False,
        risposta.status_code,
        body,
        _messaggio(risposta.status_code, body.get("error", "")),
    )


def _messaggio(status, errore):
    """Traduce la risposta del servizio in un messaggio comprensibile.

    Il servizio distingue i casi con la coppia (status HTTP, campo `error`):
    lo stesso testo "Invalid site key or secret" arriva con 404 se la site key
    è sconosciuta e con 403 se il secret è sbagliato.
    """
    if status == 429:
        return (
            "Troppe richieste di verifica. Rispetta l'header Retry-After "
            "e non ritentare in loop."
        )
    if status == 400:
        return (
            "Parametri mancanti nella richiesta di verifica: controlla di "
            f"leggere il campo '{CAMPO_TOKEN}' e di inviare 'secret' e 'response'."
        )
    if status == 403 and errore == "Token expired":
        return "Il captcha è scaduto. Risolvilo di nuovo e reinvia la form."
    if status == 403:
        return (
            "Chiave segreta non valida. È un errore di configurazione del "
            "server, non dell'utente."
        )
    if status == 404 and errore == "Token not found":
        # Causa più frequente: il token era già stato verificato una volta.
        # I token sono monouso, il servizio li cancella alla prima verifica
        # riuscita, quindi un secondo controllo è indistinguibile da un token
        # inventato.
        return (
            "Captcha non valido o già utilizzato. I token sono monouso: "
            "verificane uno una sola volta."
        )
    if status == 404:
        return "Site key sconosciuta: controlla la configurazione del server."

    return f"Verifica del captcha non riuscita (HTTP {status}): {errore or 'errore sconosciuto'}"


if __name__ == "__main__":
    # Esempio d'uso. Sostituisci i placeholder con i valori del tuo sito:
    # la site key è pubblica, la secret key va letta dalla configurazione
    # del server e non deve mai finire in un repository.
    ok, status, body, errore = verifica_captcha(
        base_url="https://captcha.tuodominio.it",
        site_key="SITE_KEY_PUBBLICA",
        secret="SECRET_KEY_PRIVATA",
        token="il-token-arrivato-dalla-form",
    )

    if ok:
        print("Captcha valido, procedo con l'elaborazione della form.")
    else:
        # Mostra all'utente un messaggio generico e logga il dettaglio:
        # `body` può contenere informazioni sulla configurazione del server.
        print(f"Captcha non valido: {errore} (HTTP {status}, body {body})")
