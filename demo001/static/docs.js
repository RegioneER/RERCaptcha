/* Pulsante "Copia" dei blocchi di codice.
 *
 * navigator.clipboard esiste solo in secure context: https, oppure
 * http://localhost. Se la demo viene aperta da un altro host in chiaro
 * (http://192.168.x.x:5001) l'API non c'e', quindi i pulsanti restano
 * nascosti anziche' presentarsi e non fare nulla.
 */
(function () {
  "use strict";

  if (!navigator.clipboard) {
    return;
  }

  // Un solo annuncio condiviso: gli screen reader leggono il cambiamento di
  // contenuto, mentre il testo del pulsante da solo non verrebbe annunciato.
  var annuncio = document.createElement("span");
  annuncio.setAttribute("role", "status");
  annuncio.setAttribute("aria-live", "polite");
  annuncio.className = "visually-hidden";
  document.body.appendChild(annuncio);

  document.querySelectorAll("[data-copia]").forEach(function (bottone) {
    bottone.hidden = false;
  });

  document.addEventListener("click", function (evento) {
    var bottone = evento.target.closest("[data-copia]");
    if (!bottone) {
      return;
    }

    var codice = bottone.closest(".code-block").querySelector("code");
    if (!codice) {
      return;
    }

    // textContent e non innerHTML: l'evidenziazione aggiunge solo <span>, il
    // testo copiato coincide con il sorgente.
    navigator.clipboard.writeText(codice.textContent).then(
      function () {
        var originale = bottone.textContent;
        bottone.textContent = "Copiato";
        annuncio.textContent = "Codice copiato negli appunti";
        setTimeout(function () {
          bottone.textContent = originale;
          annuncio.textContent = "";
        }, 2000);
      },
      function () {
        annuncio.textContent = "Copia non riuscita";
      }
    );
  });
})();
