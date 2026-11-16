"""Abnahmekriterien A1 bis A3 gegen die Originaldateien in Org_Daten.

Die 20 Bilder aus A1 landen in ausgabe/abnahme-a1/. Der Ordner ausgabe/
wird von Git ignoriert.
"""

import warnings

import pytest
from PIL import Image

from conftest import ORG_DATEN, ORIGINALE, REPO
from mandelbrot.berechnen import abbruchwerte
from mandelbrot.einfaerben import bild
from mandelbrot.original import LESETABELLE, lies_dat
from mandelbrot.paletten import palette
from mandelbrot.statistik import automatische_schwelle, bereichsbreiten, haeufigkeit
from mandelbrot.vergleich import vergleiche

ORDNER_A1 = REPO / "ausgabe" / "abnahme-a1"

# Gemessen in der Voranalyse am 16.11.2026 (technische Spec):
# Datei -> (Menge, Stufen, automatische Schwelle, Bereiche)
VORANALYSE = {
    "M0.DAT": (0.9995, 0.9985, 5, 238),
    "M01.DAT": (0.9997, 0.9923, 39, 255),
    "M1.DAT": (0.9998, 0.9941, 16, 248),
    "M11.DAT": (0.9928, 0.9174, 54, 253),
    "M12.DAT": (0.9996, 0.8608, 1, 206),
}
TOLERANZ = 0.0005


@pytest.fixture(scope="module")
def nachrechnung():
    """Rechnet jedes Original einmal nach: Datei -> (Original, Abbruchwerte)."""
    ergebnis = {}
    for name in ORIGINALE:
        original = lies_dat(ORG_DATEN / name)
        ergebnis[name] = (original, abbruchwerte(original.nachrechnung))
    return ergebnis


@pytest.mark.parametrize("name", ORIGINALE)
@pytest.mark.parametrize("nummer", [0, 1, 2, 3])
def test_a1_original_als_png(name, nummer):
    original = lies_dat(ORG_DATEN / name)
    ORDNER_A1.mkdir(parents=True, exist_ok=True)
    ziel = ORDNER_A1 / f"{name.removesuffix('.DAT')}-palette{nummer}.png"
    bild(original.stufen, palette(nummer)).save(ziel)
    with Image.open(ziel) as png:
        assert png.size == (480, 480) and png.mode == "RGB"
        # Ein Bild mit nur einer Farbe wäre ein Fehler.
        assert len(png.getcolors(maxcolors=1 << 24)) > 1


@pytest.mark.parametrize("name", ORIGINALE)
def test_a2_menge_und_a3_stufen(nachrechnung, name):
    original, roh = nachrechnung[name]
    regel = LESETABELLE[name]
    menge, stufen, _ = vergleiche(original.stufen, roh, regel.schwelle_1991)

    assert menge >= regel.grenze_menge, f"A2 verfehlt: {menge:.4f}"
    if regel.grenze_stufen is not None:
        assert stufen >= regel.grenze_stufen, f"A3 verfehlt: {stufen:.4f}"

    erwartet_menge, erwartet_stufen, _, _ = VORANALYSE[name]
    for bezeichnung, gemessen, erwartet in (
        ("Menge", menge, erwartet_menge),
        ("Stufen", stufen, erwartet_stufen),
    ):
        if abs(gemessen - erwartet) > TOLERANZ:
            warnings.warn(
                f"{name}: {bezeichnung} {gemessen:.4f} weicht von der "
                f"Voranalyse {erwartet:.4f} ab. Ursache vor der Abnahme klären."
            )


@pytest.mark.parametrize("name", ORIGINALE)
def test_automatische_schwelle_wie_in_der_voranalyse(nachrechnung, name):
    _, roh = nachrechnung[name]
    _, _, erwartete_schwelle, erwartete_bereiche = VORANALYSE[name]
    zaehlung = haeufigkeit(roh)
    schwelle = automatische_schwelle(zaehlung, 255)
    assert schwelle == erwartete_schwelle
    assert len(bereichsbreiten(zaehlung, schwelle, 255)) == erwartete_bereiche
