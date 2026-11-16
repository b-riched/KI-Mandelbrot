"""R14: Statistik bei beliebiger Abbruchgrenze, schnelle gegen einfache Fassung."""

import numpy as np
import pytest

from mandelbrot.statistik import (
    automatische_schwelle,
    bereichsbreiten,
    farbstufen,
    haeufigkeit,
    stufentabelle,
)


def _bereichsbreiten_stufe_1(zaehlung, schwelle, max_bereiche, grenze):
    """Die Fassung aus Stufe 1: durchläuft jeden Abbruchwert einzeln."""
    breiten, summe = [0], 0
    for wert in range(1, grenze + 1):
        summe += int(zaehlung[wert])
        breiten[-1] += 1
        if summe >= schwelle or wert == grenze:
            breiten.append(0)
            summe = 0
    breiten.pop()
    if len(breiten) > max_bereiche:
        breiten = breiten[:max_bereiche]
        rest = grenze - sum(breiten)
        i = max_bereiche - 1
        while rest > 0:
            anteil = rest if i == 0 else (rest + 1) // 2
            breiten[i] += anteil
            rest -= anteil
            i -= 1
    return breiten


def _automatische_schwelle_stufe_1(zaehlung, max_bereiche, grenze):
    schwelle = 1
    while len(_bereichsbreiten_stufe_1(zaehlung, schwelle, 10**9, grenze)) > max_bereiche:
        schwelle += 1
    return schwelle


def _zaehlung(saat: int, grenze: int, luecken: float) -> np.ndarray:
    """Zufällige Häufigkeiten. Ein Teil der Abbruchwerte kommt gar nicht vor."""
    rng = np.random.default_rng(saat)
    zaehlung = rng.integers(0, 40, grenze + 2)
    zaehlung[rng.random(grenze + 2) < luecken] = 0
    return zaehlung


@pytest.mark.parametrize("grenze", [10, 1005, 5000])
@pytest.mark.parametrize("luecken", [0.0, 0.5, 0.97])
@pytest.mark.parametrize("schwelle", [0, 1, 2, 7, 50, 1000, 10**7])
@pytest.mark.parametrize("max_bereiche", [1, 16, 255, 256, 10**9])
def test_schnelle_fassung_gleich_der_aus_stufe_1(grenze, luecken, schwelle, max_bereiche):
    zaehlung = _zaehlung(grenze, grenze, luecken)
    schnell = bereichsbreiten(zaehlung, schwelle, max_bereiche, grenze)
    assert schnell == _bereichsbreiten_stufe_1(zaehlung, schwelle, max_bereiche, grenze)
    assert sum(schnell) == grenze


@pytest.mark.parametrize("grenze", [10, 300, 1005])
@pytest.mark.parametrize("saat", [1, 2, 3])
@pytest.mark.parametrize("max_bereiche", [1, 16, 255])
def test_halbierung_gleich_der_suche_aus_stufe_1(grenze, saat, max_bereiche):
    zaehlung = _zaehlung(saat, grenze, 0.3)
    assert automatische_schwelle(zaehlung, max_bereiche, grenze) == (
        _automatische_schwelle_stufe_1(zaehlung, max_bereiche, grenze)
    )


def test_leeres_bild():
    # Kein einziger Punkt außerhalb der Menge: ein Bereich, Schwelle 1.
    zaehlung = np.zeros(5002, int)
    assert bereichsbreiten(zaehlung, 1, 255, 5000) == [5000]
    assert automatische_schwelle(zaehlung, 255, 5000) == 1


def test_tabelle_und_farbstufen_bei_grenze_5000():
    grenze = 5000
    roh = np.array([[1, 2500], [5000, 5001]], np.int32)
    zaehlung = haeufigkeit(roh, grenze)
    assert len(zaehlung) == grenze + 2
    breiten = bereichsbreiten(zaehlung, 1, 255, grenze)
    assert breiten == [1, 2499, 2500]
    tabelle = stufentabelle(breiten)
    assert len(tabelle) == grenze + 2
    assert farbstufen(roh, tabelle).tolist() == [[1, 2], [3, 0]]
