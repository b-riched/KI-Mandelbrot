"""Abnahmekriterien B1, B4, B7 und B8 der Stufe 2a.

Die Bilder aus B1 und die gemessenen Rechenzeiten landen in
ausgabe/abnahme-b1/. Der Ordner ausgabe/ wird von Git ignoriert.
"""

import time

import numpy as np
import pytest
from PIL import Image

from conftest import REPO
from mandelbrot.berechnen import berechne_bild
from mandelbrot.einfaerben import bild as faerbe
from mandelbrot.paletten import palette
from mandelbrot.statistik import (
    automatische_schwelle,
    bereichsbreiten,
    farbstufen,
    haeufigkeit,
    stufentabelle,
)
from mandelbrot.typen import GROESSEN, Bildausschnitt

ORDNER_B1 = REPO / "ausgabe" / "abnahme-b1"
ZEITEN = ORDNER_B1 / "rechenzeiten.txt"
# Ansicht der ganzen Menge
MITTE_X, MITTE_Y, BREITE = "-0.75", "0", "3.5"


@pytest.fixture(scope="module", autouse=True)
def zeitenliste():
    ORDNER_B1.mkdir(parents=True, exist_ok=True)
    ZEITEN.write_text(
        "Rechenzeit auf dem Prozessor, ganze Menge, Abbruchgrenze 1005\n", encoding="utf-8"
    )


@pytest.mark.parametrize("groesse", [*GROESSEN, "1000x700"])
def test_b1_bild_in_jeder_groesse(groesse):
    ausschnitt = Bildausschnitt.aus_text(MITTE_X, MITTE_Y, BREITE, groesse)
    start = time.perf_counter()
    roh, glatt, warnungen = berechne_bild(ausschnitt)
    dauer = time.perf_counter() - start
    assert warnungen == []
    form = (ausschnitt.pixel_b, ausschnitt.pixel_h)
    assert roh.shape == form
    assert glatt.shape == form and glatt.dtype == np.float32  # B7

    zaehlung = haeufigkeit(roh)
    breiten = bereichsbreiten(zaehlung, automatische_schwelle(zaehlung))
    assert sum(breiten) == 1005 and len(breiten) <= 255
    stufen = farbstufen(roh, stufentabelle(breiten))
    ziel = ORDNER_B1 / f"{groesse}.png"
    faerbe(stufen, palette(1)).save(ziel)
    with Image.open(ziel) as png:
        assert png.size == form and png.mode == "RGB"

    # Die Menge liegt in der Bildmitte, die Ecken liegen außerhalb.
    assert roh[form[0] // 2, form[1] // 2] == 1006
    assert roh[0, 0] < 1006 and roh[-1, -1] < 1006
    # Die Menge ist zur x-Achse symmetrisch, das Bild also zur waagerechten Mitte.
    assert np.array_equal(roh, roh[:, ::-1])

    with ZEITEN.open("a", encoding="utf-8") as datei:
        datei.write(f"{groesse:>9}  {form[0]} x {form[1]}  {dauer:6.1f} s\n")  # B8


def test_b4_abbruchgrenze_5000():
    grenze = 5000
    ausschnitt = Bildausschnitt.aus_text(
        "-0.743643887037151", "0.131825904205330", "0.00001", "320x180"
    )
    roh, glatt, _ = berechne_bild(ausschnitt, grenze)
    assert roh.min() >= 1 and roh.max() <= grenze + 1
    # Mit 1005 Schritten wären viele dieser Punkte noch nicht entschieden.
    assert ((roh > 1005) & (roh <= grenze)).sum() > 100
    zaehlung = haeufigkeit(roh, grenze)
    schwelle = automatische_schwelle(zaehlung, 255, grenze)
    breiten = bereichsbreiten(zaehlung, schwelle, 255, grenze)
    assert sum(breiten) == grenze and len(breiten) <= 255
    stufen = farbstufen(roh, stufentabelle(breiten))
    assert stufen.max() == len(breiten)
    assert (stufen[roh == grenze + 1] == 0).all()
