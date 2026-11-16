"""R21, R22, R23: der Arbeiter, vom Job bis zum Ergebnis."""

import json
import time

import numpy as np
import pytest
from PIL import Image

from mandelbrot import arbeiter, berechnen, warteschlange
from mandelbrot.kommandozeile import main
from stufe3 import KLEIN, ereignisse, lege_ergebnis, lege_job, projekt, protokollzeilen


@pytest.fixture
def werte(tmp_path):
    return projekt(tmp_path)


def _lauf(werte, name):
    return json.loads((werte.ergebnisse / name / "lauf.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------ C1: ein Job


def test_job_datei_wird_zum_ergebnis(werte):
    lege_job(werte, "gesamt", {**KLEIN, "serie": "probe", "notiz": "erster"})
    assert arbeiter.arbeite(werte, einmal=True) == 1

    assert warteschlange.stand_von(werte, "gesamt") == "fertig"
    ordner = werte.ergebnisse / "gesamt"
    assert sorted(p.name for p in ordner.iterdir()) == [
        "bild.png", "glatt.npy", "lauf.json", "roh.npy", "stufen.npy",
    ]
    with Image.open(ordner / "bild.png") as png:
        assert png.size == (48, 32)
    assert np.load(ordner / "roh.npy").shape == (48, 32)

    lauf = _lauf(werte, "gesamt")
    assert lauf["herkunft"] == "berechnet" and lauf["format"] == 2
    assert lauf["bild"]["mitte_x"] == "-0.75" and lauf["raster"] == [48, 32]
    assert sum(lauf["statistik"]["breiten"]) == 1005
    job = lauf["job"]
    assert job["name"] == "gesamt" and job["serie"] == "probe" and job["notiz"] == "erster"
    assert job["elternbild"] is None and job["warnungen"] == []
    assert job["angelegt"] <= job["gestartet"] <= job["fertig"]
    assert job["rechenzeit_sekunden"] >= 0
    # Von Hand abgelegt: Das Protokoll nennt "entdeckt" statt "angelegt".
    assert ereignisse(werte, "gesamt") == ["entdeckt", "gestartet", "fertig"]
    assert not any(p.name.endswith(".teil") for p in werte.ergebnisse.iterdir())


def test_angelegt_aus_dem_job_wird_uebernommen(werte):
    lege_job(werte, "vom-server", {**KLEIN, "angelegt": "2026-11-16T12:00:00+01:00"})
    arbeiter.arbeite(werte, einmal=True)
    assert _lauf(werte, "vom-server")["job"]["angelegt"] == "2026-11-16T12:00:00+01:00"
    assert ereignisse(werte, "vom-server") == ["gestartet", "fertig"]


def test_elternbild_gibt_die_bildgroesse_vor(werte):
    lege_job(werte, "eltern", {**KLEIN, "groesse": "40x24"}, alter=30)
    kind = {"mitte_x": "-0.7436", "mitte_y": "0.1318", "breite": "0.01", "elternbild": "eltern"}
    lege_job(werte, "kind", kind, alter=10)
    assert arbeiter.arbeite(werte, einmal=True) == 2
    lauf = _lauf(werte, "kind")
    assert lauf["raster"] == [40, 24] and lauf["job"]["elternbild"] == "eltern"


def test_abbruchgrenze_palette_und_schwelle_aus_dem_job(werte):
    lege_job(werte, "eigen", {**KLEIN, "abbruchgrenze": 60, "palette": 2, "schwelle": 3,
                              "max_bereiche": 256})
    arbeiter.arbeite(werte, einmal=True)
    lauf = _lauf(werte, "eigen")
    assert lauf["abbruchgrenze"] == 60 and lauf["palette"] == 2
    assert lauf["statistik"]["schwelle"] == 3 and lauf["statistik"]["max_bereiche"] == 256
    assert sum(lauf["statistik"]["breiten"]) == 60


def test_warnung_steht_im_ergebnis_und_im_protokoll(werte):
    lege_job(werte, "tief", {"mitte_x": "0.1", "mitte_y": "0.1", "breite": "5e-13",
                             "groesse": "32x32", "abbruchgrenze": 20})
    arbeiter.arbeite(werte, einmal=True)
    assert warteschlange.stand_von(werte, "tief") == "fertig"
    assert len(_lauf(werte, "tief")["job"]["warnungen"]) == 1
    assert "warnung" in ereignisse(werte, "tief")


# --------------------------------------------------------- C2: Fehler


def test_fehlerhafter_job_haelt_die_warteschlange_nicht_auf(werte):
    lege_job(werte, "kaputt", {**KLEIN, "mitte_x": -0.75}, alter=30)
    lege_job(werte, "gut", alter=10)
    assert arbeiter.arbeite(werte, einmal=True) == 2

    assert warteschlange.stand_von(werte, "kaputt") == "fehler"
    grund = warteschlange.fehlertext_datei(werte, "kaputt").read_text(encoding="utf-8")
    assert "Anführungszeichen" in grund and "Traceback" not in grund
    assert not (werte.ergebnisse / "kaputt").exists()
    assert ereignisse(werte, "kaputt") == ["entdeckt", "gestartet", "fehler"]
    assert warteschlange.stand_von(werte, "gut") == "fertig"
    assert (werte.ergebnisse / "gut" / "bild.png").is_file()


def test_unlesbare_job_datei(werte):
    lege_job(werte, "muell", roh="{das ist kein json")
    arbeiter.arbeite(werte, einmal=True)
    assert warteschlange.stand_von(werte, "muell") == "fehler"
    assert "kein gültiges JSON" in warteschlange.fehlertext_datei(werte, "muell").read_text(
        encoding="utf-8"
    )


def test_vorhandenes_ergebnis_wird_nicht_ueberschrieben(werte):
    alt = lege_ergebnis(werte, "doppelt")
    (alt / "merkmal.txt").write_text("alt", encoding="utf-8")
    lege_job(werte, "doppelt")
    arbeiter.arbeite(werte, einmal=True)
    assert warteschlange.stand_von(werte, "doppelt") == "fehler"
    assert "schon ein Ergebnis" in warteschlange.fehlertext_datei(werte, "doppelt").read_text(
        encoding="utf-8"
    )
    assert (alt / "merkmal.txt").read_text(encoding="utf-8") == "alt"


def test_unerwarteter_fehler_mit_fehlerspur(werte, monkeypatch):
    def geht_schief(*args, **kwargs):
        raise RuntimeError("Speicher voll")

    lege_job(werte, "pech", alter=30)
    lege_job(werte, "danach", alter=10)
    monkeypatch.setattr(berechnen, "berechne_bild", geht_schief)
    assert arbeiter.arbeite(werte, einmal=True) == 2
    grund = warteschlange.fehlertext_datei(werte, "pech").read_text(encoding="utf-8")
    assert "Unerwarteter Fehler: RuntimeError: Speicher voll" in grund
    assert "Traceback" in grund
    assert warteschlange.stand_von(werte, "danach") == "fehler"  # der Arbeiter lief weiter
    assert not any(werte.ergebnisse.iterdir())


# ------------------------------------------------------- C3: Neustart


def test_abbruch_mitten_im_job_und_neustart(werte, monkeypatch):
    echt = berechnen.berechne_bild

    def strg_c(*args, **kwargs):
        raise KeyboardInterrupt

    lege_job(werte, "lang", alter=30)
    lege_job(werte, "wartet", alter=10)
    monkeypatch.setattr(berechnen, "berechne_bild", strg_c)
    with pytest.raises(KeyboardInterrupt):
        arbeiter.arbeite(werte, einmal=True)

    # Der Job ist nicht verloren: Er liegt in "laeuft", ein Ergebnis gibt es nicht.
    assert warteschlange.stand_von(werte, "lang") == "laeuft"
    assert warteschlange.stand_von(werte, "wartet") == "neu"
    assert not any(werte.ergebnisse.iterdir())
    assert arbeiter.lies_lebenszeichen(werte)["aktiv"] is False
    # Reste eines halben Ergebnisses, wie nach einem Stromausfall:
    halb = warteschlange.teilordner(werte, "lang")
    halb.mkdir()
    (halb / "roh.npy").write_bytes(b"halb")

    monkeypatch.setattr(berechnen, "berechne_bild", echt)
    assert arbeiter.arbeite(werte, einmal=True) == 2
    assert warteschlange.stand_von(werte, "lang") == "fertig"
    assert warteschlange.stand_von(werte, "wartet") == "fertig"
    assert (werte.ergebnisse / "lang" / "bild.png").is_file() and not halb.exists()
    assert ereignisse(werte, "lang") == [
        "entdeckt", "gestartet", "zurueckgestellt", "entdeckt", "gestartet", "fertig",
    ]
    # Der zurückgestellte Job behält seinen Platz vor dem jüngeren.
    fertig = [zeile[1] for zeile in protokollzeilen(werte) if zeile[2] == "fertig"]
    assert fertig == ["lang", "wartet"]


def test_ergebnis_erscheint_erst_wenn_es_vollstaendig_ist(werte, monkeypatch):
    from mandelbrot import ablage

    echt = ablage.schreibe_lauf
    gesehen = {}

    def beobachte(ordner, **mehr):
        gesehen["ziel_vorhanden"] = (werte.ergebnisse / "gesamt").exists()
        gesehen["schreibt_nach"] = ordner.name
        return echt(ordner, **mehr)

    monkeypatch.setattr(ablage, "schreibe_lauf", beobachte)
    lege_job(werte, "gesamt")
    arbeiter.arbeite(werte, einmal=True)
    assert gesehen == {"ziel_vorhanden": False, "schreibt_nach": "gesamt.teil"}
    assert (werte.ergebnisse / "gesamt" / "lauf.json").is_file()


# ---------------------------------------------- Schleife und Lebenszeichen


def test_junge_datei_wird_erst_spaeter_gerechnet(werte):
    lege_job(werte, "frisch", alter=0)
    assert arbeiter.arbeite(werte, einmal=True) == 0
    assert warteschlange.stand_von(werte, "frisch") == "neu"
    assert arbeiter.arbeite(werte, einmal=True, mindestalter=0) == 1


def test_schleife_wartet_und_endet_auf_wunsch(werte, monkeypatch):
    pausen = []
    monkeypatch.setattr(time, "sleep", pausen.append)
    assert arbeiter.arbeite(werte, soll_enden=lambda: len(pausen) >= 3) == 0
    assert pausen == [werte.pause_sekunden] * 3
    ohne_job = [zeile[2] for zeile in protokollzeilen(werte) if zeile[1] == "-"]
    assert ohne_job == ["arbeiter gestartet", "arbeiter beendet"]


def test_lebenszeichen(werte):
    assert arbeiter.lies_lebenszeichen(werte) == {"aktiv": False, "job": None, "zeit": None}
    arbeiter.schreibe_lebenszeichen(werte, None)
    assert arbeiter.lies_lebenszeichen(werte)["aktiv"] is True
    arbeiter.schreibe_lebenszeichen(werte, "lang")
    zeichen = arbeiter.lies_lebenszeichen(werte)
    assert zeichen["aktiv"] is True and zeichen["job"] == "lang"
    arbeiter.schreibe_lebenszeichen(werte, None, beendet=True)
    assert arbeiter.lies_lebenszeichen(werte)["aktiv"] is False


def test_altes_lebenszeichen_gilt_nicht_mehr(werte):
    datei = werte.jobs / arbeiter.LEBENSZEICHEN
    datei.write_text(
        json.dumps({"zeit": "2026-11-16T10:00:00+01:00", "job": None}), encoding="utf-8"
    )
    assert arbeiter.lies_lebenszeichen(werte)["aktiv"] is False
    datei.write_text("kaputt", encoding="utf-8")
    assert arbeiter.lies_lebenszeichen(werte)["aktiv"] is False


# ------------------------------------------------------------ der Befehl


def test_befehl_arbeiter_einmal(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    werte = projekt(tmp_path)
    lege_job(werte, "gesamt")
    assert main(["arbeiter", "--einmal"]) == 0
    assert "Bearbeitete Jobs: 1" in capsys.readouterr().out
    assert (tmp_path / "_ERGEBNISSE" / "gesamt" / "bild.png").is_file()
    assert (tmp_path / "_JOBS" / "fertig" / "gesamt.json").is_file()


def test_befehl_arbeiter_legt_die_ordner_an(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert main(["arbeiter", "--einmal"]) == 0
    assert (tmp_path / "_JOBS" / "neu").is_dir() and (tmp_path / "_EVENTS").is_dir()


def test_befehl_arbeiter_mit_einstellungen(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mandelbrot.toml").write_text('[ordner]\nergebnisse = "Bilder"\n', encoding="utf-8")
    werte = projekt(tmp_path)
    lege_job(werte, "gesamt")
    assert main(["arbeiter", "--einmal"]) == 0
    assert (tmp_path / "Bilder" / "gesamt" / "bild.png").is_file()


def test_befehl_arbeiter_mit_fehlerhaften_einstellungen(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mandelbrot.toml").write_text("[server]\nport = 0\n", encoding="utf-8")
    assert main(["arbeiter", "--einmal"]) == 2
    assert "port" in capsys.readouterr().err
