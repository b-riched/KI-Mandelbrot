"""Abnahmekriterien C1, C2, C5 und C6 der Stufe 3 im Zusammenspiel.

Drei Jobs gehen über den Job-Server: einer wird gerechnet, einer ist
fehlerhaft und wird abgewiesen, einer übernimmt die Größe seines
Elternbildes. Ein vierter liegt fehlerhaft von Hand in der Warteschlange.
Gerechnet wird mit dem Befehl `arbeiter --einmal`.
"""

import json
import os
import time

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from mandelbrot import server
from mandelbrot.kommandozeile import main
from stufe3 import ereignisse, lege_job, projekt, protokollzeilen

GESAMT = {"mitte_x": "-0.75", "mitte_y": "0", "breite": "3.5", "groesse": "60x40", "palette": 2}
AUSSCHNITT = {"mitte_x": "-0.75", "mitte_y": "0.1", "breite": "0.5", "elternbild": "gesamt",
              "serie": "seepferdchen", "notiz": "aus der Mitte"}


def _lasse_altern(werte):
    """Der Arbeiter lässt frische Dateien zwei Sekunden liegen (R20). Der Test wartet nicht."""
    zeit = time.time() - 10
    for datei in werte.ordner_fuer("neu").glob("*.json"):
        os.utime(datei, (zeit, zeit))


@pytest.fixture(scope="module")
def ablauf(tmp_path_factory):
    ordner = tmp_path_factory.mktemp("abnahme-3")
    werte = projekt(ordner)
    seite = TestClient(server.erzeuge_app(werte))
    antworten = {}
    alt = os.getcwd()
    os.chdir(ordner)
    try:
        antworten["gesamt"] = seite.post("/api/jobs", json={**GESAMT, "name": "gesamt"})
        # Fehlerhaft: keine Bildgröße und kein Elternbild (R19).
        antworten["abgewiesen"] = seite.post(
            "/api/jobs", json={"mitte_x": "-0.75", "mitte_y": "0", "breite": "1", "name": "ohne"}
        )
        # Fehlerhaft und von Hand abgelegt: Das merkt erst der Arbeiter. Er ist
        # der älteste Job und kommt deshalb vor 'gesamt' an die Reihe.
        lege_job(werte, "von-hand", {**GESAMT, "abbruchgrenze": 5}, alter=3600)
        _lasse_altern(werte)
        antworten["lauf_1"] = main(["arbeiter", "--einmal"])
        antworten["wartend_1"] = seite.get("/api/jobs?stand=neu").json()

        # Das Elternbild muss als Ergebnis da sein, bevor der Ausschnitt angelegt wird.
        antworten["ausschnitt"] = seite.post("/api/jobs", json={**AUSSCHNITT, "name": "ausschnitt"})
        _lasse_altern(werte)
        antworten["lauf_2"] = main(["arbeiter", "--einmal"])
    finally:
        os.chdir(alt)
    return werte, seite, antworten


def test_anlegen_ueber_den_job_server(ablauf):
    werte, seite, antworten = ablauf
    assert antworten["gesamt"].status_code == 201
    assert antworten["ausschnitt"].status_code == 201
    assert antworten["lauf_1"] == 0 and antworten["lauf_2"] == 0
    assert antworten["wartend_1"] == []


def test_c5_ohne_groesse_und_elternbild_abgewiesen(ablauf):
    werte, seite, antworten = ablauf
    assert antworten["abgewiesen"].status_code == 400
    assert "Bildgröße" in antworten["abgewiesen"].json()["fehler"]
    assert seite.get("/api/jobs/ohne").status_code == 404
    assert ereignisse(werte, "ohne") == []


def test_c1_stand_der_jobs(ablauf):
    werte, seite, antworten = ablauf
    staende = {job["name"]: job["stand"] for job in seite.get("/api/jobs").json()}
    assert staende == {"gesamt": "fertig", "ausschnitt": "fertig", "von-hand": "fehler"}
    zustand = seite.get("/api/zustand").json()
    assert zustand["jobs"] == {"neu": 0, "laeuft": 0, "fertig": 2, "fehler": 1}
    assert zustand["ergebnisse"] == 2 and zustand["arbeiter_aktiv"] is False


def test_c2_fehlerhafter_job_mit_meldung_und_der_naechste_laeuft(ablauf):
    werte, seite, antworten = ablauf
    job = seite.get("/api/jobs/von-hand").json()
    assert job["stand"] == "fehler" and "Abbruchgrenze" in job["fehler"]
    text = (werte.ordner_fuer("fehler") / "von-hand.fehler.txt").read_text(encoding="utf-8")
    assert job["fehler"] in text
    # 'von-hand' war der älteste Job. 'gesamt' wurde trotzdem danach gerechnet.
    reihenfolge = [zeile[1] for zeile in protokollzeilen(werte) if zeile[2] == "gestartet"]
    assert reihenfolge == ["von-hand", "gesamt", "ausschnitt"]
    assert seite.get("/api/ergebnisse/von-hand").status_code == 404


def test_c5_groesse_des_elternbildes(ablauf):
    werte, seite, antworten = ablauf
    assert "groesse" not in antworten["ausschnitt"].json()["angaben"]
    lauf = seite.get("/api/ergebnisse/ausschnitt").json()
    assert lauf["raster"] == [60, 40]
    assert lauf["job"]["elternbild"] == "gesamt" and lauf["job"]["serie"] == "seepferdchen"
    assert lauf["job"]["notiz"] == "aus der Mitte"
    assert lauf["bild"]["breite"] == "0.5"


def test_ergebnisse_und_bild(ablauf):
    werte, seite, antworten = ablauf
    ergebnisse = seite.get("/api/ergebnisse").json()
    assert sorted(e["name"] for e in ergebnisse) == ["ausschnitt", "gesamt"]
    for ergebnis in ergebnisse:
        assert ergebnis["raster"] == [60, 40]
        antwort = seite.get(ergebnis["bild"])
        assert antwort.status_code == 200 and antwort.headers["content-type"] == "image/png"
        datei = werte.ergebnisse / ergebnis["name"] / "bild.png"
        assert antwort.content == datei.read_bytes()
        with Image.open(datei) as png:
            assert png.size == (60, 40)
    nach_name = {e["name"]: e for e in ergebnisse}
    assert nach_name["ausschnitt"]["elternbild"] == "gesamt"
    assert nach_name["gesamt"]["elternbild"] is None
    assert seite.get("/api/ergebnisse/gesamt").json()["palette"] == 2


def test_c6_protokoll(ablauf):
    werte, seite, antworten = ablauf
    assert ereignisse(werte, "gesamt") == ["angelegt", "gestartet", "fertig"]
    assert ereignisse(werte, "ausschnitt") == ["angelegt", "gestartet", "fertig"]
    assert ereignisse(werte, "von-hand") == ["entdeckt", "gestartet", "fehler"]
    assert ereignisse(werte, "-") == ["arbeiter gestartet", "arbeiter beendet"] * 2
    for zeile in protokollzeilen(werte):
        assert len(zeile) == 4
    # Die Zeiten in der Beschreibung des Laufs passen zum Protokoll.
    job = json.loads((werte.ergebnisse / "gesamt" / "lauf.json").read_text(encoding="utf-8"))["job"]
    angelegt = [z[0] for z in protokollzeilen(werte) if z[1:3] == ["gesamt", "angelegt"]]
    assert angelegt == [job["angelegt"]]
    assert job["angelegt"] <= job["gestartet"] <= job["fertig"]
