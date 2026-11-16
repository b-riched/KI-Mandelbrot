"""R3: von Abbruchwerten zu Farbstufen."""

import numpy as np
import pytest

from mandelbrot.statistik import (
    automatische_schwelle,
    bereichsbreiten,
    farbstufen,
    haeufigkeit,
    pruefe_einstellungen,
    stufentabelle,
)
from mandelbrot.typen import Eingabefehler


def _leer() -> np.ndarray:
    return np.zeros(1007, int)


def test_bereiche_von_hand():
    zaehlung = _leer()
    zaehlung[1], zaehlung[2], zaehlung[3] = 5, 5, 10
    # Werte 1 und 2 erreichen zusammen die Schwelle, Wert 3 allein,
    # alle übrigen Werte kommen nicht vor und landen im letzten Bereich.
    assert bereichsbreiten(zaehlung, 10) == [2, 1, 1002]


def test_schwelle_null_gibt_jedem_wert_einen_bereich():
    assert bereichsbreiten(_leer(), 0, 10**6) == [1] * 1005


def test_restverteilung_wie_1991():
    breiten = bereichsbreiten(_leer(), 0, 256)
    assert len(breiten) == 256
    assert sum(breiten) == 1005
    assert breiten[:246] == [1] * 246
    assert breiten[-10:] == [2, 2, 4, 7, 13, 24, 48, 95, 188, 376]


def test_restverteilung_bei_sehr_kleiner_hoechstzahl():
    assert bereichsbreiten(_leer(), 0, 3) == [251, 252, 502]
    assert bereichsbreiten(_leer(), 0, 1) == [1005]


@pytest.mark.parametrize("schwelle", [0, 1, 7, 50, 1000, 10**6])
@pytest.mark.parametrize("max_bereiche", [1, 16, 255, 256])
def test_summe_der_breiten_ist_immer_1005(schwelle, max_bereiche):
    zaehlung = np.random.default_rng(1).integers(0, 40, 1007)
    breiten = bereichsbreiten(zaehlung, schwelle, max_bereiche)
    assert sum(breiten) == 1005
    assert len(breiten) <= max_bereiche
    assert all(breite >= 1 for breite in breiten)


def test_stufentabelle_waechst_mit_dem_abbruchwert():
    zaehlung = np.random.default_rng(2).integers(0, 40, 1007)
    breiten = bereichsbreiten(zaehlung, 30, 255)
    tabelle = stufentabelle(breiten)
    assert tabelle[0] == 0 and tabelle[1006] == 0
    assert tabelle[1] == 1 and tabelle[1005] == len(breiten)
    assert (np.diff(tabelle[1:1006]) >= 0).all()
    assert (np.diff(tabelle[1:1006]) <= 1).all()


def test_farbstufen_und_haeufigkeit():
    roh = np.array([[1, 3], [1006, 4]], np.int16)
    zaehlung = haeufigkeit(roh)
    assert zaehlung[1] == 1 and zaehlung[3] == 1 and zaehlung[1006] == 1
    tabelle = stufentabelle([2, 1, 1002])
    assert farbstufen(roh, tabelle).tolist() == [[1, 2], [0, 3]]


@pytest.mark.parametrize("saat", [3, 4, 5])
def test_automatische_schwelle_ist_die_kleinste_passende(saat):
    zaehlung = np.random.default_rng(saat).integers(0, 60, 1007)
    schwelle = automatische_schwelle(zaehlung, 255)
    assert len(bereichsbreiten(zaehlung, schwelle, 10**6)) <= 255
    assert schwelle == 1 or len(bereichsbreiten(zaehlung, schwelle - 1, 10**6)) > 255


def test_falsche_einstellungen():
    with pytest.raises(Eingabefehler):
        pruefe_einstellungen(-1, 255)
    with pytest.raises(Eingabefehler):
        pruefe_einstellungen(5, 0)
    with pytest.raises(Eingabefehler):
        pruefe_einstellungen(5, 257)
