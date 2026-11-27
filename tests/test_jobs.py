"""R18, R19: Job-Dateien prüfen, lesen und schreiben."""

import json

import pytest

from mandelbrot import jobs
from mandelbrot.typen import Eingabefehler
from stufe3 import KLEIN, lege_ergebnis, projekt


@pytest.fixture
def werte(tmp_path):
    return projekt(tmp_path)


def test_kleinster_job_bekommt_die_standardwerte(werte):
    job = jobs.pruefe(dict(KLEIN), "probe", werte)
    assert job.name == "probe"
    assert (job.bild.pixel_b, job.bild.pixel_h) == (48, 32)
    assert job.bild.als_text()["mitte_x"] == "-0.75"
    assert job.abbruchgrenze == 1005 and job.palette == 1
    assert job.schwelle == "auto" and job.max_bereiche == 255
    assert job.elternbild is None and job.serie is None
    assert job.notiz == "" and job.angelegt is None


def test_alle_angaben(werte):
    lege_ergebnis(werte, "gesamt")
    angaben = {
        "mitte_x": "-0.743643887037151", "mitte_y": "0,131825904205330",
        "breite": "0.00001", "groesse": "FullHD", "abbruchgrenze": 5000, "palette": 2,
        "schwelle": 12, "max_bereiche": 256, "elternbild": "gesamt",
        "serie": "seepferdchen", "notiz": "erster Versuch",
        "angelegt": "2026-11-16T22:20:00+01:00",
    }
    job = jobs.pruefe(angaben, "tief-01", werte)
    assert (job.bild.pixel_b, job.bild.pixel_h) == (1920, 1080)
    assert job.bild.als_text()["mitte_y"] == "0.131825904205330"
    assert (job.abbruchgrenze, job.palette, job.schwelle, job.max_bereiche) == (5000, 2, 12, 256)
    assert (job.elternbild, job.serie, job.notiz) == ("gesamt", "seepferdchen", "erster Versuch")
    assert job.angelegt == "2026-11-16T22:20:00+01:00"


def test_schwelle_auto_in_jeder_schreibweise(werte):
    assert jobs.pruefe({**KLEIN, "schwelle": " AUTO "}, "probe", werte).schwelle == "auto"
    assert jobs.pruefe({**KLEIN, "schwelle": 0}, "probe", werte).schwelle == 0


@pytest.mark.parametrize(
    "aenderung, stichwort",
    [
        ({"mitte_x": None}, "fehlt: mitte_x"),
        ({"breite": None}, "fehlt: breite"),
        ({"mitte_x": -0.75}, "Anführungszeichen"),
        ({"breite": 3}, "Anführungszeichen"),
        ({"mitte_y": "oben"}, "keine Zahl"),
        ({"breite": "0"}, "größer als 0"),
        ({"farbe": "rot"}, "Unbekannte Angabe im Job: farbe"),
        ({"name": "x"}, "Unbekannte Angabe im Job: name"),
        ({"groesse": "riesig"}, "Bildgröße"),
        ({"groesse": [48, 32]}, "'groesse'"),
        ({"abbruchgrenze": 5}, "Abbruchgrenze"),
        ({"abbruchgrenze": "1005"}, "ganze Zahl"),
        ({"abbruchgrenze": True}, "ganze Zahl"),
        ({"palette": 7}, "'palette'"),
        ({"palette": "1"}, "ganze Zahl"),
        ({"schwelle": -1}, "Schwelle"),
        ({"schwelle": "viel"}, "'schwelle'"),
        ({"schwelle": 1.5}, "'schwelle'"),
        ({"max_bereiche": 0}, "Höchstzahl"),
        ({"max_bereiche": 300}, "Höchstzahl"),
        ({"elternbild": "gibt-es-nicht"}, "Elternbild"),
        ({"elternbild": 5}, "'elternbild'"),
        ({"elternbild": "../geheim"}, "nicht erlaubt"),
        ({"serie": 3}, "'serie'"),
        ({"notiz": ["a"]}, "'notiz'"),
        ({"breite": "1e-14", "groesse": "wqhd"}, "zu klein"),
    ],
)
def test_fehlerhafte_angaben(werte, aenderung, stichwort):
    angaben = {**KLEIN, **aenderung}
    angaben = {feld: wert for feld, wert in angaben.items() if wert is not None}
    with pytest.raises(Eingabefehler) as fehler:
        jobs.pruefe(angaben, "probe", werte)
    assert stichwort in str(fehler.value)


@pytest.mark.parametrize("name", ["a/b", "..", "", "a:b"])
def test_unerlaubter_jobname(werte, name):
    with pytest.raises(Eingabefehler):
        jobs.pruefe(dict(KLEIN), name, werte)


# ------------------------------------------------------------------- R19


def test_r19_angegebene_groesse_gilt_auch_mit_elternbild(werte):
    lege_ergebnis(werte, "eltern", raster=(1920, 1080))
    job = jobs.pruefe({**KLEIN, "groesse": "64x48", "elternbild": "eltern"}, "kind", werte)
    assert (job.bild.pixel_b, job.bild.pixel_h) == (64, 48)


def test_r19_ohne_groesse_gilt_die_des_elternbildes(werte):
    lege_ergebnis(werte, "eltern", raster=(2360, 1640))
    angaben = {feld: wert for feld, wert in KLEIN.items() if feld != "groesse"}
    job = jobs.pruefe({**angaben, "elternbild": "eltern"}, "kind", werte)
    assert (job.bild.pixel_b, job.bild.pixel_h) == (2360, 1640)


def test_r19_ohne_groesse_und_ohne_elternbild_ist_ein_fehler(werte):
    angaben = {feld: wert for feld, wert in KLEIN.items() if feld != "groesse"}
    with pytest.raises(Eingabefehler, match="fehlt die Bildgröße"):
        jobs.pruefe(angaben, "kind", werte)


# ---------------------------------------------------- lesen und schreiben


def test_schreiben_und_lesen(tmp_path):
    datei = tmp_path / "neu" / "probe.json"
    jobs.schreibe(datei, {**KLEIN, "notiz": "Größe"})
    assert jobs.lies(datei) == {**KLEIN, "notiz": "Größe"}
    assert [p.name for p in datei.parent.iterdir()] == ["probe.json"]  # keine halbe Datei
    assert "Größe" in datei.read_text(encoding="utf-8")


def test_datei_aus_dem_windows_editor_mit_bom(tmp_path):
    datei = tmp_path / "probe.json"
    datei.write_bytes(b"\xef\xbb\xbf" + json.dumps(KLEIN).encode("utf-8"))
    assert jobs.lies(datei) == KLEIN


@pytest.mark.parametrize("inhalt", ['{"mitte_x": "0",', "", "[1, 2]", '"nur text"'])
def test_unlesbare_datei(tmp_path, inhalt):
    datei = tmp_path / "probe.json"
    datei.write_text(inhalt, encoding="utf-8")
    with pytest.raises(Eingabefehler):
        jobs.lies(datei)
