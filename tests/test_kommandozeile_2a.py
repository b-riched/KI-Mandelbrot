"""Stufe 2a: der Befehl berechne mit Mittelpunkt, Bildbreite und Bildgröße."""

import json

import numpy as np
import pytest
from PIL import Image

from mandelbrot import berechnen
from mandelbrot.kommandozeile import main

# Weit außerhalb der Menge: Die Rechnung ist sofort fertig.
AUSSEN = ["--mitte-x=2,5", "--mitte-y=2,5", "--breite=1"]
SCHNELL_1991 = ["--xmin=0,5", "--xmax=2", "--ymin=0,5", "--ymax=2"]


@pytest.fixture(autouse=True)
def im_temporaeren_ordner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _beschreibung(tmp_path, name):
    return json.loads((tmp_path / "ausgabe" / name / "lauf.json").read_text(encoding="utf-8"))


def test_neue_form_mit_freier_groesse(tmp_path):
    assert main(["berechne", *AUSSEN, "--groesse", "64x48", "--name", "neu"]) == 0
    ordner = tmp_path / "ausgabe" / "neu"
    assert sorted(p.name for p in ordner.iterdir()) == [
        "bild.png", "glatt.npy", "lauf.json", "roh.npy", "stufen.npy",
    ]
    inhalt = _beschreibung(tmp_path, "neu")
    assert inhalt["format"] == 2
    assert inhalt["bild"] == {
        "mitte_x": "2.5", "mitte_y": "2.5", "breite": "1", "lage": "aufrecht",
    }
    assert "ausschnitt" not in inhalt
    assert inhalt["raster"] == [64, 48]
    assert inhalt["abbruchgrenze"] == 1005 and inhalt["wert_in_menge"] == 1006
    with Image.open(ordner / "bild.png") as png:
        assert png.size == (64, 48)
    assert np.load(ordner / "roh.npy").shape == (64, 48)
    glatt = np.load(ordner / "glatt.npy")
    assert glatt.shape == (64, 48) and glatt.dtype == np.float32


def test_neue_form_mit_benannter_groesse(tmp_path):
    assert main(["berechne", *AUSSEN, "--groesse", "hd", "--name", "hd"]) == 0
    assert _beschreibung(tmp_path, "hd")["raster"] == [1280, 720]
    with Image.open(tmp_path / "ausgabe" / "hd" / "bild.png") as png:
        assert png.size == (1280, 720)


def test_abbruchgrenze_in_der_neuen_form(tmp_path):
    befehl = ["berechne", "--mitte-x=0", "--mitte-y=0", "--breite=1", "--groesse", "32x32",
              "--abbruchgrenze", "50", "--name", "kurz"]
    assert main(befehl) == 0
    inhalt = _beschreibung(tmp_path, "kurz")
    assert inhalt["abbruchgrenze"] == 50 and inhalt["wert_in_menge"] == 51
    assert sum(inhalt["statistik"]["breiten"]) == 50
    assert np.load(tmp_path / "ausgabe" / "kurz" / "roh.npy").max() == 51


def test_abbruchgrenze_in_der_form_wie_1991(tmp_path):
    befehl = ["berechne", *SCHNELL_1991, "--abbruchgrenze", "50", "--name", "alt"]
    assert main(befehl) == 0
    inhalt = _beschreibung(tmp_path, "alt")
    assert inhalt["abbruchgrenze"] == 50 and inhalt["lage"] == "wie 1991"
    assert inhalt["raster"] == [480, 480] and "bild" not in inhalt
    assert sum(inhalt["statistik"]["breiten"]) == 50
    # Die Form wie 1991 bleibt wie in Stufe 1, ohne gebrochene Abbruchwerte.
    assert not (tmp_path / "ausgabe" / "alt" / "glatt.npy").exists()


def test_faerbe_auf_einem_neuen_lauf_rechnet_nicht_neu(tmp_path, monkeypatch):
    befehl = ["berechne", "--mitte-x=-0,75", "--mitte-y=0", "--breite=3,5",
              "--groesse", "96x54", "--abbruchgrenze", "200", "--name", "quelle"]
    assert main(befehl) == 0

    def darf_nicht_laufen(*args, **kwargs):
        raise AssertionError("faerbe hat neu gerechnet")

    monkeypatch.setattr(berechnen, "rechne", darf_nicht_laufen)
    assert main(["faerbe", "ausgabe/quelle", "--palette", "2", "--schwelle", "9",
                 "--name", "bunt"]) == 0
    quelle, bunt = _beschreibung(tmp_path, "quelle"), _beschreibung(tmp_path, "bunt")
    assert bunt["herkunft"] == "neu eingefärbt" and bunt["aus_lauf"] == "quelle"
    assert bunt["bild"] == quelle["bild"] and bunt["raster"] == [96, 54]
    assert bunt["abbruchgrenze"] == 200
    assert bunt["statistik"]["schwelle"] == 9 and sum(bunt["statistik"]["breiten"]) == 200
    for name in ("roh.npy", "glatt.npy"):
        assert (tmp_path / "ausgabe" / "quelle" / name).read_bytes() == (
            tmp_path / "ausgabe" / "bunt" / name
        ).read_bytes()
    with Image.open(tmp_path / "ausgabe" / "bunt" / "bild.png") as png:
        assert png.size == (96, 54)


def test_lauf_im_format_1_bleibt_lesbar(tmp_path):
    assert main(["berechne", *SCHNELL_1991, "--name", "alt"]) == 0
    datei = tmp_path / "ausgabe" / "alt" / "lauf.json"
    inhalt = json.loads(datei.read_text(encoding="utf-8"))
    # So sah die Beschreibung in Stufe 1 aus: Format 1, ohne Angabe der Lage.
    inhalt["format"] = 1
    del inhalt["lage"]
    datei.write_text(json.dumps(inhalt), encoding="utf-8")
    assert main(["faerbe", "ausgabe/alt", "--palette", "0", "--name", "alt-weiss"]) == 0
    neu = _beschreibung(tmp_path, "alt-weiss")
    assert neu["format"] == 2 and neu["ausschnitt"] == inhalt["ausschnitt"]


def test_warnung_an_der_genauigkeitsgrenze(tmp_path, capsys):
    befehl = ["berechne", "--mitte-x=0,1", "--mitte-y=0,1", "--breite=5e-13",
              "--groesse", "32x32", "--abbruchgrenze", "20", "--name", "tief"]
    assert main(befehl) == 0
    assert "Warnung:" in capsys.readouterr().err
    assert (tmp_path / "ausgabe" / "tief" / "bild.png").exists()


@pytest.mark.parametrize(
    "befehl, stichwort",
    [
        (["berechne", *AUSSEN, "--groesse", "hd", "--xmin=0"], "nur eine Form"),
        (["berechne", *AUSSEN], "--groesse"),
        (["berechne", "--mitte-x=0", "--breite=1", "--groesse", "hd"], "--mitte-y"),
        (["berechne", *AUSSEN, "--groesse", "riesig"], "Bildgröße"),
        (["berechne", *AUSSEN, "--groesse", "8x8"], "zwischen 16 und 10000"),
        (["berechne", "--mitte-x=0", "--mitte-y=0", "--breite=0", "--groesse", "hd"], "größer als 0"),
        (["berechne", "--mitte-x=abc", "--mitte-y=0", "--breite=1", "--groesse", "hd"], "keine Zahl"),
        (["berechne", *AUSSEN, "--groesse", "hd", "--abbruchgrenze", "5"], "Abbruchgrenze"),
        (["berechne", *AUSSEN, "--groesse", "hd", "--abbruchgrenze", "viel"], "Abbruchgrenze"),
        (["berechne", *SCHNELL_1991, "--abbruchgrenze", "2000000"], "Abbruchgrenze"),
        (["berechne", "--mitte-x=-1,75", "--mitte-y=0", "--breite=1e-14", "--groesse", "wqhd"], "zu klein"),
        (["berechne"], "Es fehlt der Ausschnitt"),
    ],
)
def test_falsche_eingaben_ergeben_rueckgabewert_2(befehl, stichwort, tmp_path, capsys):
    assert main(befehl) == 2
    meldung = capsys.readouterr().err
    assert meldung.startswith("Fehler: ") and stichwort in meldung
    assert not (tmp_path / "ausgabe").exists()
