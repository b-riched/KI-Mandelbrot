"""R17, R20, R23: Reihenfolge, Verschieben und Aufräumen nach einem Neustart."""

import pytest

from mandelbrot import warteschlange
from stufe3 import KLEIN, ereignisse, lege_ergebnis, lege_job, projekt


@pytest.fixture
def werte(tmp_path):
    return projekt(tmp_path)


def test_leere_warteschlange(werte):
    assert warteschlange.naechster(werte) is None


def test_aeltester_job_zuerst_nach_aenderungsdatum(werte):
    lege_job(werte, "zweiter", alter=20)
    lege_job(werte, "erster", alter=30)
    lege_job(werte, "dritter", alter=10)
    assert warteschlange.naechster(werte).stem == "erster"


def test_angabe_angelegt_geht_vor_aenderungsdatum(werte):
    # Die Datei "frueh" ist jünger, wurde laut Angabe aber früher angelegt.
    lege_job(werte, "spaet", {**KLEIN, "angelegt": "2026-11-16T12:00:00+01:00"}, alter=60)
    lege_job(werte, "frueh", {**KLEIN, "angelegt": "2026-11-16T11:00:00+01:00"}, alter=10)
    assert warteschlange.naechster(werte).stem == "frueh"


def test_bei_gleichstand_entscheidet_der_name(werte):
    gleich = {**KLEIN, "angelegt": "2026-11-16T12:00:00+01:00"}
    lege_job(werte, "b", gleich)
    lege_job(werte, "a", gleich)
    assert warteschlange.naechster(werte).stem == "a"


def test_unlesbare_datei_reiht_sich_nach_aenderungsdatum_ein(werte):
    lege_job(werte, "kaputt", roh="{kein json", alter=50)
    lege_job(werte, "gut", alter=10)
    assert warteschlange.naechster(werte).stem == "kaputt"


def test_junge_dateien_bleiben_liegen(werte):
    lege_job(werte, "frisch", alter=0)
    assert warteschlange.naechster(werte) is None
    assert warteschlange.naechster(werte, mindestalter=0).stem == "frisch"
    lege_job(werte, "alt", alter=5)
    assert warteschlange.naechster(werte).stem == "alt"


def test_andere_dateien_werden_uebersehen(werte):
    neu = werte.ordner_fuer("neu")
    (neu / "halb.json.teil").write_text("{}", encoding="utf-8")
    (neu / "notiz.txt").write_text("hallo", encoding="utf-8")
    (neu / "unterordner.json").mkdir()
    assert warteschlange.naechster(werte, mindestalter=0) is None
    assert warteschlange.jobs_im_stand(werte, "neu") == []


def test_verschieben_und_stand(werte):
    lege_job(werte, "probe")
    assert warteschlange.stand_von(werte, "probe") == "neu"
    ziel = warteschlange.verschiebe(werte, "probe", "neu", "laeuft")
    assert ziel == werte.ordner_fuer("laeuft") / "probe.json" and ziel.is_file()
    assert warteschlange.stand_von(werte, "probe") == "laeuft"
    assert not (werte.ordner_fuer("neu") / "probe.json").exists()
    assert warteschlange.stand_von(werte, "unbekannt") is None


@pytest.mark.parametrize("stand", ["neu", "laeuft", "fertig", "fehler"])
def test_name_ist_vergeben_durch_einen_job(werte, stand):
    assert not warteschlange.name_vergeben(werte, "probe")
    lege_job(werte, "probe", stand=stand)
    assert warteschlange.name_vergeben(werte, "probe")


def test_name_ist_vergeben_durch_ein_ergebnis(werte):
    lege_ergebnis(werte, "bild")
    assert warteschlange.name_vergeben(werte, "bild")


def test_aufraeumen_nach_neustart(werte):
    lege_job(werte, "unterbrochen", stand="laeuft")
    lege_job(werte, "wartet")
    lege_job(werte, "erledigt", stand="fertig")
    halb = warteschlange.teilordner(werte, "unterbrochen")
    halb.mkdir()
    (halb / "roh.npy").write_bytes(b"halb")
    ganz = lege_ergebnis(werte, "erledigt")

    assert warteschlange.raeume_auf(werte) == ["unterbrochen"]
    assert warteschlange.stand_von(werte, "unterbrochen") == "neu"
    assert warteschlange.stand_von(werte, "wartet") == "neu"
    assert warteschlange.stand_von(werte, "erledigt") == "fertig"
    assert not halb.exists() and ganz.is_dir()
    assert ereignisse(werte, "unterbrochen") == ["zurueckgestellt"]
    assert warteschlange.raeume_auf(werte) == []


def test_aufraeumen_legt_fehlende_ordner_an(tmp_path):
    from mandelbrot import einstellungen

    werte = einstellungen.lade(tmp_path)  # noch kein einziger Ordner
    assert warteschlange.raeume_auf(werte) == []
    assert werte.ordner_fuer("neu").is_dir() and werte.ergebnisse.is_dir()
