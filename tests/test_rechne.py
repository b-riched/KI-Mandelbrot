"""R12, R13: Rechenkern, Abbruchgrenze und gebrochene Abbruchwerte."""

import numpy as np
import pytest

from mandelbrot.berechnen import abbruchwerte, berechne_bild, rechne
from mandelbrot.typen import Ausschnitt, Bildausschnitt


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


def _abbruchwerte_stufe_1(ausschnitt, raster=480, grenze=1005):
    """Der Rechenweg aus Stufe 1, unverändert als Vergleichsmaßstab."""
    xmin, xmax = float(ausschnitt.xmin), float(ausschnitt.xmax)
    ymin, ymax = float(ausschnitt.ymin), float(ausschnitt.ymax)
    seite_x = (xmax - xmin) / raster
    seite_y = (ymax - ymin) / raster
    nummer = np.arange(1, raster + 1)
    cx = (nummer * seite_x + xmin)[:, None] * np.ones((1, raster))
    cy = np.ones((raster, 1)) * (nummer * seite_y + ymin)[None, :]
    zx = np.zeros((raster, raster))
    zy = np.zeros((raster, raster))
    zaehler = np.zeros((raster, raster), np.int16)
    aktiv = np.ones((raster, raster), bool)
    for _ in range(grenze + 1):
        hx = zx * zx - zy * zy + cx
        hy = 2 * zx * zy + cy
        zx = np.where(aktiv, hx, zx)
        zy = np.where(aktiv, hy, zy)
        zaehler += aktiv
        aktiv &= (zx * zx + zy * zy) < 4
        if not aktiv.any():
            break
    return zaehler


def test_gleich_der_schleife_von_hand():
    cx = np.array([-2.0, -1.3, -0.7436, -0.1, 0.3, 0.26])
    cy = np.array([1.1, 0.65, 0.1318, 0.0, -0.4])
    roh, glatt = rechne(cx, cy, 80)
    assert roh.shape == (6, 5) and roh.dtype == np.int32
    assert glatt.shape == (6, 5) and glatt.dtype == np.float32
    for i, x in enumerate(cx):
        for j, y in enumerate(cy):
            assert roh[i, j] == _von_hand(float(x), float(y), 80), (i, j)


@pytest.mark.parametrize(
    "koordinaten",
    [("-0.429", "0.201", "-1.215", "-0.585"), ("-0.1443", "-0.0504", "-1.0008", "-0.9063")],
)
def test_gleich_dem_rechenweg_aus_stufe_1(koordinaten):
    ausschnitt = Ausschnitt.aus_text(*koordinaten)
    neu = abbruchwerte(ausschnitt)
    assert neu.dtype == np.int16
    assert np.array_equal(neu, _abbruchwerte_stufe_1(ausschnitt))


def test_ergebnis_haengt_nicht_von_der_blockgroesse_ab():
    cx = np.linspace(-2.1, 0.6, 50)
    cy = np.linspace(1.2, -1.2, 37)
    roh, glatt = rechne(cx, cy, 300)
    for block in (1, 7, 50, 1000):
        roh_b, glatt_b = rechne(cx, cy, 300, block=block)
        assert np.array_equal(roh, roh_b) and np.array_equal(glatt, glatt_b)


@pytest.mark.parametrize("grenze", [10, 50, 5000])
def test_punkt_der_menge_hat_grenze_plus_1(grenze):
    roh, glatt = rechne(np.array([0.0, 3.0]), np.array([0.0]), grenze)
    assert roh[0, 0] == grenze + 1 and glatt[0, 0] == 0
    assert roh[1, 0] == 1 and glatt[1, 0] != 0


def test_zahlentyp_bei_grosser_abbruchgrenze():
    aussen = Ausschnitt.aus_text("3", "4", "3", "4")
    assert abbruchwerte(aussen, raster=4, grenze=32766).dtype == np.int16
    assert abbruchwerte(aussen, raster=4, grenze=32767).dtype == np.int32


def test_gebrochene_abbruchwerte():
    bild = Bildausschnitt.aus_text("-0.75", "0", "3.5", "160x90")
    roh, glatt, warnungen = berechne_bild(bild, 300)
    assert warnungen == []
    in_menge = roh == 301
    assert in_menge.any() and (~in_menge).any()
    assert np.isfinite(glatt).all()
    assert (glatt[in_menge] == 0).all()
    # Innerhalb eines Bandes mit gleichem ganzem Abbruchwert verläuft der
    # gebrochene Wert stufenlos: Er nimmt viele verschiedene Werte an.
    band = roh == 3
    assert band.sum() > 100
    # (Das Bild ist zur x-Achse symmetrisch, jeder Wert kommt also zweimal vor.)
    assert len(np.unique(glatt[band])) > band.sum() // 4
    # Der gebrochene Wert folgt dem ganzen: Er liegt nie weit davon entfernt.
    abstand = glatt[~in_menge] - roh[~in_menge]
    assert abstand.min() > 0 and abstand.max() < 8


def test_gebrochene_werte_weit_aussen_ohne_spruenge():
    # Weit außerhalb der Menge haben benachbarte Punkte fast denselben Wert.
    _, glatt = rechne(np.linspace(2.5, 4, 64), np.linspace(4, 2.5, 64), 100)
    assert np.abs(np.diff(glatt, axis=0)).max() < 1
    assert np.abs(np.diff(glatt, axis=1)).max() < 1


def test_bild_steht_aufrecht():
    bild = Bildausschnitt.aus_text("-0.5", "0.6", "1.5", "60x40")
    roh, _, _ = berechne_bild(bild, 100)
    a = 1.5 / 60
    oben = 0.6 + (40 - 1) / 2 * a  # y-Koordinate der obersten Zeile
    links = -0.5 - (60 - 1) / 2 * a
    for spalte in (0, 17, 59):
        assert roh[spalte, 0] == _von_hand(links + spalte * a, oben, 100)
    assert roh.shape == (60, 40)
