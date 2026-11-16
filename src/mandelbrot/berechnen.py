"""Berechnung der Abbruchwerte (R1, R2), portiert aus MANDELDA.PAS."""

from __future__ import annotations

import numpy as np

from .typen import ABBRUCHGRENZE, RASTER, Ausschnitt


def abbruchwerte(
    ausschnitt: Ausschnitt, raster: int = RASTER, grenze: int = ABBRUCHGRENZE
) -> np.ndarray:
    """Liefert die Abbruchwerte als Feld [Spalte, Zeile].

    Werte 1 bis grenze: Punkt außerhalb der Menge. Wert grenze + 1: Punkt
    der Menge. Die Reihenfolge der Rechenschritte entspricht dem Original
    und darf nicht umgestellt werden, sonst ändern sich einzelne Randpunkte.
    """
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
