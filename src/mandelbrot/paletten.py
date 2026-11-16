"""Die vier Originalpaletten (R4), portiert aus MANDPAL.PAS."""

from __future__ import annotations

import numpy as np

from .typen import Eingabefehler

ANZAHL_PALETTEN = 4
_GESAETTIGT = 255

# Je Palette: Abschnittslänge, Schrittweiten (Rot, Grün, Blau) je Abschnitt,
# und der Abschnitt, vor dem alle drei Werte auf 0 gesetzt werden (oder None).
_PALETTE_1 = (
    16,
    [(0, 0, 1)] * 3
    + [(1, 0, 1), (1, 0, 0)]
    + [(1, 0, -1)] * 3
    + [(0, 0, -1)]
    + [(0, 1, 0)] * 7,
    None,
)
_TABELLEN = {
    0: (
        8,
        [
            (0, 0, 3), (1, 1, 2), (1, 1, 3), (1, 1, 1), (1, 1, 0), (1, 1, 0),
            (1, 1, 0), (0, 0, 0), (1, 1, 0), (0, 0, 0), (1, 1, 0),
        ]
        + [(0, 0, 0)] * 21,
        None,
    ),
    1: _PALETTE_1,
    2: (
        16,
        [(1, 0, 0)] * 3
        + [(1, 1, 0), (0, 1, 0), (0, 2, 1), (0, 0, 1)]
        + [(0, 0, 0)] * 9,
        7,
    ),
    3: _PALETTE_1,  # im Quelltext identisch mit Palette 1
}


def palette(nummer: int) -> np.ndarray:
    """Liefert die Palette als Feld (256, 3) mit Rot, Grün, Blau in 8 Bit."""
    if nummer not in _TABELLEN:
        raise Eingabefehler(f"Palette muss 0, 1, 2 oder 3 sein, angegeben: {nummer}")
    laenge, abschnitte, nullen_vor = _TABELLEN[nummer]
    sechs_bit = np.zeros((257, 3), int)
    farbe = [0, 0, 0]
    for k, schritt in enumerate(abschnitte):
        if nullen_vor is not None and k == nullen_vor:
            farbe = [0, 0, 0]
        for index in range(k * laenge + 1, k * laenge + laenge + 1):
            for kanal in range(3):
                farbe[kanal] += schritt[kanal]
                if farbe[kanal] >= 64:
                    farbe[kanal] = _GESAETTIGT
            sechs_bit[index] = farbe
        farbe = [64 if wert == _GESAETTIGT else wert for wert in farbe]
    sechs_bit[0] = 0
    sechs_bit = sechs_bit[:256]  # Farbe 256 liegt außerhalb der Tabelle
    acht_bit = np.where(
        sechs_bit == _GESAETTIGT,
        255,
        np.rint(np.clip(sechs_bit, 0, 63) * 255 / 63),
    )
    return acht_bit.astype(np.uint8)
