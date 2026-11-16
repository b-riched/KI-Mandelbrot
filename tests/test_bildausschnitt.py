"""R9, R10, R11, R15: Bildgröße, Mittelpunkt und Bildbreite, Lage, Genauigkeit."""

import numpy as np
import pytest

from mandelbrot.berechnen import koordinaten, pruefe_genauigkeit
from mandelbrot.typen import Bildausschnitt, Eingabefehler, lies_groesse, pruefe_abbruchgrenze


@pytest.mark.parametrize(
    "text, erwartet",
    [
        ("hd", (1280, 720)),
        ("fullhd", (1920, 1080)),
        ("wqhd", (2560, 1440)),
        ("ipad", (2360, 1640)),
        ("FullHD", (1920, 1080)),
        ("800x600", (800, 600)),
        ("800X600", (800, 600)),
        ("800×600", (800, 600)),
        (" 16 x 10000 ", (16, 10000)),
    ],
)
def test_bildgroessen(text, erwartet):
    assert lies_groesse(text) == erwartet


@pytest.mark.parametrize("text", ["riesig", "800", "800x", "x600", "15x600", "800x10001", "8.5x6"])
def test_falsche_bildgroessen(text):
    with pytest.raises(Eingabefehler):
        lies_groesse(text)


@pytest.mark.parametrize("grenze", [9, 0, -5, 1_000_001])
def test_abbruchgrenze_ausserhalb_der_grenzen(grenze):
    with pytest.raises(Eingabefehler):
        pruefe_abbruchgrenze(grenze)


def test_abbruchgrenze_an_den_raendern():
    assert pruefe_abbruchgrenze(10) == 10
    assert pruefe_abbruchgrenze(1_000_000) == 1_000_000


def test_eingaben_bleiben_als_text_erhalten():
    lang = "-0.743643887037158704752191506114774"
    bild = Bildausschnitt.aus_text(lang, "0,131825904205330", "0,0000000000010", "hd")
    assert bild.als_text() == {
        "mitte_x": lang,
        "mitte_y": "0.131825904205330",
        "breite": "0.0000000000010",
        "lage": "aufrecht",
    }
    assert (bild.pixel_b, bild.pixel_h) == (1280, 720)


@pytest.mark.parametrize("breite", ["0", "-1", "abc"])
def test_falsche_bildbreite(breite):
    with pytest.raises(Eingabefehler):
        Bildausschnitt.aus_text("0", "0", breite, "hd")


def test_mittelpunkt_liegt_in_der_bildmitte_bei_ungerader_groesse():
    cx, cy, a = koordinaten(Bildausschnitt.aus_text("-0.5", "0.25", "2", "21x17"))
    assert cx[10] == -0.5 and cy[8] == 0.25


def test_mittelpunkt_liegt_in_der_bildmitte_bei_gerader_groesse():
    cx, cy, a = koordinaten(Bildausschnitt.aus_text("-0.5", "0.25", "2", "20x16"))
    assert (cx[9] + cx[10]) / 2 == pytest.approx(-0.5, abs=1e-15)
    assert (cy[7] + cy[8]) / 2 == pytest.approx(0.25, abs=1e-15)


def test_bildpunkte_sind_quadratisch_und_das_bild_steht_aufrecht():
    bild = Bildausschnitt.aus_text("-0.75", "0", "3.5", "fullhd")
    cx, cy, a = koordinaten(bild)
    assert len(cx) == 1920 and len(cy) == 1080
    assert a == pytest.approx(3.5 / 1920)
    assert np.allclose(np.diff(cx), a) and np.allclose(np.diff(cy), -a)
    assert cy[0] > cy[-1]  # Zeile 1 ist oben und hat die größte y-Koordinate
    # Linker und rechter Bildrand liegen eine halbe Punktbreite außerhalb.
    assert cx[0] - a / 2 == pytest.approx(-0.75 - 1.75)
    assert cx[-1] + a / 2 == pytest.approx(-0.75 + 1.75)


def test_keine_warnung_bei_gewoehnlichen_bildern():
    assert pruefe_genauigkeit(Bildausschnitt.aus_text("-0.75", "0", "3.5", "wqhd")) == []


def test_warnung_unter_bildbreite_1e_12():
    warnungen = pruefe_genauigkeit(Bildausschnitt.aus_text("0.1", "0.1", "5e-13", "hd"))
    assert len(warnungen) == 1 and "unter" in warnungen[0]


def test_warnung_dicht_an_der_grenze():
    # Gemessen: bei 2560 Bildpunkten und 1e-12 sind alle Spalten verschieden,
    # der Punktabstand beträgt aber nur noch 3 bis 4 kleinste Schritte.
    bild = Bildausschnitt.aus_text("-0.743643887037151", "0.131825904205330", "1e-12", "wqhd")
    cx, cy, _ = koordinaten(bild)
    assert len(np.unique(cx)) == 2560 and len(np.unique(cy)) == 1440
    warnungen = pruefe_genauigkeit(bild)
    assert len(warnungen) == 1 and "Rechengenauigkeit" in warnungen[0]


@pytest.mark.parametrize("mitte_x", ["-1.75", "1.9", "-0.743643887037151"])
def test_fehler_wenn_bildpunkte_zusammenfallen(mitte_x):
    with pytest.raises(Eingabefehler, match="zu klein"):
        pruefe_genauigkeit(Bildausschnitt.aus_text(mitte_x, "0", "1e-14", "wqhd"))
