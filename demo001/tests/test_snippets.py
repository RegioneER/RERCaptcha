"""Test di coerenza fra demo, partial e snippet mostrati nella guida.

Non testano il comportamento del servizio captcha (non è raggiungibile da
qui): verificano che il codice mostrato agli sviluppatori non possa
silenziosamente tornare a divergere dal contratto reale del servizio, cioè
esattamente il problema che ha causato gli errori corretti in questo lavoro.

PHP e Java non sono eseguibili da pytest: qui vengono solo linkati/compilati
se l'interprete è disponibile nel PATH (altrimenti il controllo è saltato),
mentre la loro coerenza *funzionale* è verificata dai test testuali sotto.
"""

import inspect
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from snippets.verify import CAMPO_TOKEN, verifica_captcha  # noqa: E402

PARTIALS_DIR = BASE_DIR / "templates" / "partials"
SNIPPETS_DIR = BASE_DIR / "snippets"

FILE_SERVER = [
    SNIPPETS_DIR / "verify.py",
    SNIPPETS_DIR / "verify.php",
    SNIPPETS_DIR / "Verify.java",
]


def test_ordine_loader():
    """widget.js va caricato DOPO aver impostato CAP_CUSTOM_WASM_URL.

    Altrimenti il widget scarica il modulo WebAssembly da cdn.jsdelivr.net
    invece che dal servizio configurato (vedi guida, sezione "Client — widget
    visibile"). Se questo test fallisce dopo una modifica al loader, la
    modifica ha reintrodotto quel comportamento.
    """
    testo = (PARTIALS_DIR / "loader.html").read_text(encoding="utf-8")
    assert testo.index("CAP_CUSTOM_WASM_URL") < testo.index("widget.js")


def test_nome_campo_coerente():
    """Il nome del campo hidden dev'essere lo stesso ovunque compaia.

    app.py non contiene la stringa letterale: importa CAMPO_TOKEN da
    snippets.verify, che è una garanzia di coerenza più forte del grep (se il
    nome cambiasse in un posto solo, il codice smetterebbe di funzionare,
    non solo la documentazione).
    """
    testo_app = (BASE_DIR / "app.py").read_text(encoding="utf-8")
    assert "from snippets.verify import" in testo_app
    assert "CAMPO_TOKEN" in testo_app

    for f in [PARTIALS_DIR / "widget_visibile.html", PARTIALS_DIR / "form_invisibile.html", *FILE_SERVER]:
        testo = f.read_text(encoding="utf-8")
        assert CAMPO_TOKEN in testo, f"'{CAMPO_TOKEN}' non trovato in {f.relative_to(BASE_DIR)}"


@pytest.mark.parametrize("file", FILE_SERVER, ids=lambda f: f.name)
def test_contratto_siteverify(file):
    """Ogni esempio server deve rispettare il contratto reale del servizio.

    POST verso un path che termina con /siteverify, parametri "secret" e
    "response" — non "token", non "g-recaptcha-response" (contratto di altri
    servizi di captcha, da cui capita di copiare codice per errore).
    """
    testo = file.read_text(encoding="utf-8")
    assert "/siteverify" in testo
    assert "secret" in testo
    assert "response" in testo
    assert "g-recaptcha-response" not in testo


def test_nessun_host_hardcoded():
    """Gli esempi devono usare placeholder, non l'host di produzione.

    Era uno dei problemi della documentazione precedente: gli snippet
    funzionavano solo per chi guardava la demo in produzione, ed erano
    sbagliati per chi la guardava in locale.
    """
    host_produzione = "captcha.regione.emr.it"
    for f in list(PARTIALS_DIR.glob("*.html")) + FILE_SERVER:
        testo = f.read_text(encoding="utf-8")
        assert host_produzione not in testo, (
            f"{f.relative_to(BASE_DIR)} contiene l'host di produzione hardcoded; "
            "deve arrivare da una variabile o restare un placeholder"
        )


def test_attributi_documentati():
    """Ogni attributo data-cap-* usato nei partial è nella tabella di riferimento."""
    import capjs_reference as ref

    attrs_documentati = {r["attributo"] for r in ref.DATA_ATTRS}
    i18n_documentate = {r["chiave"] for r in ref.I18N_KEYS}

    for f in PARTIALS_DIR.glob("*.html"):
        testo = f.read_text(encoding="utf-8")
        for attr in re.findall(r'data-cap-(?!i18n-)([a-z-]+)=', testo):
            nome_completo = f"data-cap-{attr}"
            assert nome_completo in attrs_documentati, (
                f"{nome_completo} usato in {f.name} ma assente da DATA_ATTRS"
            )
        for chiave in re.findall(r'data-cap-i18n-([a-z-]+)=', testo):
            assert chiave in i18n_documentate, (
                f"data-cap-i18n-{chiave} usato in {f.name} ma assente da I18N_KEYS"
            )


def test_snippet_python_importabile():
    """La firma dell'esempio Python deve restare quella pubblicata."""
    firma = inspect.signature(verifica_captcha)
    assert list(firma.parameters) == [
        "base_url",
        "site_key",
        "secret",
        "token",
        "timeout",
    ]


def test_snippet_php_lint():
    if not shutil.which("php"):
        pytest.skip("php non disponibile nel PATH")
    risultato = subprocess.run(
        ["php", "-l", str(SNIPPETS_DIR / "verify.php")],
        capture_output=True,
        text=True,
    )
    assert risultato.returncode == 0, risultato.stdout + risultato.stderr


def test_snippet_java_compila(tmp_path):
    if not shutil.which("javac"):
        pytest.skip("javac non disponibile nel PATH")
    # javac richiede che il nome del file corrisponda alla classe pubblica.
    sorgente = tmp_path / "Verify.java"
    sorgente.write_text((SNIPPETS_DIR / "Verify.java").read_text(encoding="utf-8"))
    risultato = subprocess.run(
        ["javac", "-d", str(tmp_path), str(sorgente)],
        capture_output=True,
        text=True,
    )
    assert risultato.returncode == 0, risultato.stdout + risultato.stderr
