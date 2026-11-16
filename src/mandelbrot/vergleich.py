"""Vergleich einer Neuberechnung mit dem Original (R7)."""

from __future__ import annotations

import numpy as np
from PIL import Image

from .einfaerben import bild
from .statistik import (
    MAX_BEREICHE_1991,
    bereichsbreiten,
    farbstufen,
    haeufigkeit,
    stufentabelle,
)
from .typen import WERT_IN_MENGE

_ABSTAND = 10
_FARBE_ABSTAND = (128, 128, 128)
_FARBE_GLEICH = (48, 48, 48)
_FARBE_ABWEICHUNG = (255, 255, 255)


def vergleiche(
    original_stufen: np.ndarray,
    roh: np.ndarray,
    schwelle: int,
    max_bereiche: int = MAX_BEREICHE_1991,
) -> tuple[float, float, np.ndarray]:
    """Liefert Mengen-Übereinstimmung, Stufen-Übereinstimmung und neue Farbstufen."""
    in_menge = roh == WERT_IN_MENGE
    menge = ((original_stufen == 0) == in_menge).mean()
    breiten = bereichsbreiten(haeufigkeit(roh), schwelle, max_bereiche)
    neu = farbstufen(roh, stufentabelle(breiten))
    stufen = (neu == original_stufen).mean()
    return float(menge), float(stufen), neu


def vergleichsbild(
    original_stufen: np.ndarray, neue_stufen: np.ndarray, palette: np.ndarray
) -> Image.Image:
    """Drei Felder nebeneinander: Original, Neuberechnung, Abweichungen."""
    links = bild(original_stufen, palette)
    mitte = bild(neue_stufen, palette)
    gleich = (original_stufen == neue_stufen).T  # Lage [Zeile, Spalte]
    rechts_rgb = np.where(
        gleich[:, :, None],
        np.array(_FARBE_GLEICH, np.uint8),
        np.array(_FARBE_ABWEICHUNG, np.uint8),
    ).astype(np.uint8)
    rechts = Image.fromarray(rechts_rgb)
    breite, hoehe = links.size
    gesamt = Image.new("RGB", (3 * breite + 2 * _ABSTAND, hoehe), _FARBE_ABSTAND)
    for nummer, feld in enumerate((links, mitte, rechts)):
        gesamt.paste(feld, (nummer * (breite + _ABSTAND), 0))
    return gesamt
