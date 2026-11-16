"""R1 und R2: Raster und Abbruchwerte."""

import numpy as np

from mandelbrot.berechnen import abbruchwerte
from mandelbrot.typen import Ausschnitt


def _von_hand(cx: float, cy: float, grenze: int) -> int:
    """Die Schleife aus MANDELDA.PAS für einen einzelnen Punkt."""
    zx = zy = 0.0
    zaehler = 0
    while zx * zx + zy * zy < 4 and zaehler <= grenze:
        hx = zx * zx - zy * zy + cx
        hy = 2 * zx * zy + cy
        zx, zy = hx, hy
        zaehler += 1
    return zaehler


def test_punkte_mit_betrag_ab_2_haben_abbruchwert_1():
    roh = abbruchwerte(Ausschnitt.aus_text("3", "4", "3", "4"), raster=4, grenze=50)
    assert (roh == 1).all()


def test_der_punkt_null_gehoert_zur_menge():
    # Mit xmin = -1, xmax = 1 und Raster 4 liegt Spalte 2 genau bei cx = 0.
    roh = abbruchwerte(Ausschnitt.aus_text("-1", "1", "-1", "1"), raster=4, grenze=50)
    assert roh[1, 1] == 51


def test_zuordnung_von_bildpunkt_zu_koordinate():
    xmin, xmax, ymin, ymax = -2.0, 0.5, -1.2, 0.4
    raster, grenze = 4, 60
    roh = abbruchwerte(
        Ausschnitt.aus_text("-2", "0.5", "-1.2", "0.4"), raster=raster, grenze=grenze
    )
    for x in range(1, raster + 1):
        for y in range(1, raster + 1):
            cx = x * ((xmax - xmin) / raster) + xmin
            cy = y * ((ymax - ymin) / raster) + ymin
            assert roh[x - 1, y - 1] == _von_hand(cx, cy, grenze), (x, y)
    # Das Feld ist nicht symmetrisch, eine vertauschte Lage fiele also auf.
    assert not np.array_equal(roh, roh.T)


def test_rechter_rand_wird_berechnet_linker_nicht():
    # Spalte 4 liegt genau bei xmax = 3 und damit außerhalb des Kreises um 0.
    roh = abbruchwerte(Ausschnitt.aus_text("-1", "3", "-0.5", "0"), raster=4, grenze=50)
    assert (roh[3, :] == 1).all()
    # Spalte 1 liegt bei cx = 0, nicht bei xmin = -1.
    assert roh[0, 3] == 51


def test_form_typ_und_wiederholbarkeit():
    ausschnitt = Ausschnitt.aus_text("-2.1", "0.6", "-1.35", "1.35")
    eins = abbruchwerte(ausschnitt, raster=32, grenze=200)
    zwei = abbruchwerte(ausschnitt, raster=32, grenze=200)
    assert eins.shape == (32, 32)
    assert eins.dtype == np.int16
    assert eins.min() >= 1 and eins.max() == 201
    assert np.array_equal(eins, zwei)
