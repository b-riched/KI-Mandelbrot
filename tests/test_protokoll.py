"""R25: das Protokoll."""

from datetime import datetime, timedelta, timezone

from mandelbrot import protokoll
from stufe3 import projekt, protokollzeilen

MEZ = timezone(timedelta(hours=1))


def test_zeile_hat_vier_felder(tmp_path):
    werte = projekt(tmp_path)
    zeit = datetime(2026, 11, 16, 22, 20, 3, tzinfo=MEZ)
    protokoll.schreibe(werte, "seepferdchen-01", "fertig", "5.8 s, 1920 x 1080", zeit)
    datei = werte.ereignisse / "2026-11-16.log"
    assert datei.read_text(encoding="utf-8") == (
        "2026-11-16T22:20:03+01:00\tseepferdchen-01\tfertig\t5.8 s, 1920 x 1080\n"
    )


def test_eine_datei_pro_tag_und_zeilen_werden_angehaengt(tmp_path):
    werte = projekt(tmp_path)
    protokoll.schreibe(werte, "a", "gestartet", zeitpunkt=datetime(2026, 11, 16, 23, 59, tzinfo=MEZ))
    protokoll.schreibe(werte, "a", "fertig", zeitpunkt=datetime(2026, 11, 17, 0, 1, tzinfo=MEZ))
    protokoll.schreibe(werte, "b", "gestartet", zeitpunkt=datetime(2026, 11, 17, 0, 2, tzinfo=MEZ))
    assert sorted(p.name for p in werte.ereignisse.iterdir()) == [
        "2026-11-16.log", "2026-11-17.log",
    ]
    assert len((werte.ereignisse / "2026-11-17.log").read_text(encoding="utf-8").splitlines()) == 2


def test_zeilenumbrueche_und_tabulatoren_im_text(tmp_path):
    werte = projekt(tmp_path)
    protokoll.schreibe(werte, "kaputt", "fehler", "erste Zeile\nzweite\tZeile\r\n  dritte")
    (zeile,) = protokollzeilen(werte)
    assert len(zeile) == 4
    assert zeile[1:] == ["kaputt", "fehler", "erste Zeile zweite Zeile dritte"]


def test_ereignis_ohne_job_und_ohne_text(tmp_path):
    werte = projekt(tmp_path)
    protokoll.schreibe(werte, protokoll.OHNE_JOB, "arbeiter gestartet")
    (zeile,) = protokollzeilen(werte)
    assert zeile[1:] == ["-", "arbeiter gestartet", ""]
    assert datetime.fromisoformat(zeile[0]).tzinfo is not None  # mit Zeitzone


def test_umlaute(tmp_path):
    werte = projekt(tmp_path)
    protokoll.schreibe(werte, "größe", "fehler", "Die Bildgröße fehlt")
    assert protokollzeilen(werte)[0][1:] == ["größe", "fehler", "Die Bildgröße fehlt"]


def test_ordner_wird_bei_bedarf_angelegt(tmp_path):
    from mandelbrot import einstellungen

    werte = einstellungen.lade(tmp_path)
    protokoll.schreibe(werte, "-", "server gestartet")
    assert len(protokollzeilen(werte)) == 1
