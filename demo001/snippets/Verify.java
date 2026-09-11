import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Verifica lato server di un token RERCaptcha.
 *
 * Non eseguito da questa demo (che è scritta in Python): la coerenza con il
 * contratto reale del servizio è garantita dai test in tests/test_snippets.py.
 *
 * Usa solo java.net.http.HttpClient (JDK 11+), senza dipendenze esterne.
 * L'estrazione manuale di "success" ed "error" dal JSON evita di introdurre
 * una libreria solo per due campi; se il progetto ne usa già una (Jackson,
 * Gson...), preferiscila.
 */
public class Verify {

    /** Esito di una verifica: successo, status HTTP e messaggio per l'utente. */
    public record Esito(boolean ok, Integer status, String corpoGrezzo, String errore) {}

    private static final Pattern SUCCESS = Pattern.compile("\"success\"\\s*:\\s*true");
    private static final Pattern ERROR = Pattern.compile("\"error\"\\s*:\\s*\"([^\"]*)\"");

    /**
     * Verifica un token RERCaptcha interrogando il servizio.
     *
     * @param baseUrl URL del servizio raggiungibile DAL TUO SERVER (non
     *                quello usato dal browser).
     * @param siteKey chiave pubblica del sito.
     * @param secret  chiave segreta. Non deve mai raggiungere il browser.
     * @param token   valore del campo "capjs-token" arrivato con la form.
     */
    public static Esito verificaCaptcha(String baseUrl, String siteKey, String secret, String token) {
        // Il token vuoto non va nemmeno inviato: il servizio risponderebbe
        // 400. Un token assente non significa necessariamente che l'utente
        // non abbia risolto il captcha: il widget svuota il campo da sé
        // quando il token scade.
        if (token == null || token.isBlank()) {
            return new Esito(false, null, "",
                "Token del captcha assente. Se avevi già risolto il captcha, è probabile che sia scaduto: risolvilo di nuovo.");
        }

        String corpo = "secret=" + urlEncode(secret) + "&response=" + urlEncode(token);
        String url = baseUrl.replaceAll("/$", "") + "/" + siteKey + "/siteverify";

        HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .header("Content-Type", "application/x-www-form-urlencoded")
            .timeout(Duration.ofSeconds(5))
            .POST(HttpRequest.BodyPublishers.ofString(corpo))
            .build();

        HttpResponse<String> risposta;
        try {
            risposta = client.send(request, HttpResponse.BodyHandlers.ofString());
        } catch (Exception e) {
            // Servizio non raggiungibile, DNS, TLS, timeout di connessione...
            // Da loggare: è un problema di infrastruttura, non dell'utente.
            return new Esito(false, null, "", "Servizio captcha non raggiungibile: " + e.getMessage());
        }

        String corpoRisposta = risposta.body();

        // ATTENZIONE: leggi il corpo anche sugli status diversi da 2xx. Il
        // servizio risponde con {"error": "..."} sui 4xx, e quel messaggio
        // va letto, non scartato.
        boolean successo = risposta.statusCode() == 200 && SUCCESS.matcher(corpoRisposta).find();
        if (successo) {
            return new Esito(true, risposta.statusCode(), corpoRisposta, null);
        }

        Matcher m = ERROR.matcher(corpoRisposta);
        String erroreServizio = m.find() ? m.group(1) : "";

        return new Esito(false, risposta.statusCode(), corpoRisposta,
            messaggioErrore(risposta.statusCode(), erroreServizio));
    }

    /**
     * Traduce la risposta del servizio in un messaggio comprensibile.
     *
     * Il servizio distingue i casi con la coppia (status HTTP, campo
     * "error"): lo stesso testo "Invalid site key or secret" arriva con 404
     * se la site key è sconosciuta e con 403 se il secret è sbagliato.
     */
    private static String messaggioErrore(int status, String errore) {
        if (status == 429) {
            return "Troppe richieste di verifica. Rispetta l'header Retry-After e non ritentare in loop.";
        }
        if (status == 400) {
            return "Parametri mancanti nella richiesta di verifica: controlla di leggere il campo 'capjs-token' e di inviare 'secret' e 'response'.";
        }
        if (status == 403 && "Token expired".equals(errore)) {
            return "Il captcha è scaduto. Risolvilo di nuovo e reinvia la form.";
        }
        if (status == 403) {
            return "Chiave segreta non valida. È un errore di configurazione del server, non dell'utente.";
        }
        if (status == 404 && "Token not found".equals(errore)) {
            // Causa più frequente: il token era già stato verificato una
            // volta. I token sono monouso: un secondo controllo è
            // indistinguibile da un token inventato.
            return "Captcha non valido o già utilizzato. I token sono monouso: verificane uno una sola volta.";
        }
        if (status == 404) {
            return "Site key sconosciuta: controlla la configurazione del server.";
        }
        return "Verifica del captcha non riuscita (HTTP " + status + "): "
            + (errore.isEmpty() ? "errore sconosciuto" : errore);
    }

    private static String urlEncode(String s) {
        return URLEncoder.encode(s, StandardCharsets.UTF_8);
    }

    // Esempio d'uso. Sostituisci i placeholder con i valori del tuo sito: la
    // site key è pubblica, la secret key va letta dalla configurazione del
    // server e non deve mai finire in un repository.
    public static void main(String[] args) {
        Esito esito = verificaCaptcha(
            "https://captcha.tuodominio.it",
            "SITE_KEY_PUBBLICA",
            "SECRET_KEY_PRIVATA",
            "il-token-arrivato-dalla-form"
        );

        if (esito.ok()) {
            System.out.println("Captcha valido, procedo con l'elaborazione della form.");
        } else {
            // Mostra all'utente un messaggio generico e logga il dettaglio.
            System.out.println("Captcha non valido: " + esito.errore()
                + " (HTTP " + esito.status() + ", corpo " + esito.corpoGrezzo() + ")");
        }
    }
}
