"""Berechnung der Abbruchwerte.

R1, R2: Raster und Rechenregel aus MANDELDA.PAS (Stufe 1).
R10 bis R13, R15: Ausschnitt durch Mittelpunkt und Bildbreite, wählbare
Abbruchgrenze, gebrochene Abbruchwerte, Grenze der Rechengenauigkeit
(Stufe 2a).
"""

from __future__ import annotations

import numpy as np

from .typen import (
    ABBRUCHGRENZE,
    RASTER,
    Ausschnitt,
    Bildausschnitt,
    Eingabefehler,
    dezimaltext,
)

BLOCK = 64  # Spalten, die gemeinsam gerechnet werden
_BETRAG_QUADRAT_GROSS = 65536.0  # |z| >= 256
_SCHRITTE_NACH_ABBRUCH = 8
WARNGRENZE_BREITE = 1e-12
_FEINHEIT_FAKTOR = 4


def _gebrochen(zx, zy, px, py, r2, schritt):
    """Gebrochener Abbruchwert für Punkte, die im Schritt `schritt` abbrechen (R13)."""
    schritte = np.full(zx.size, float(schritt))
    for _ in range(_SCHRITTE_NACH_ABBRUCH):
        klein = r2 < _BETRAG_QUADRAT_GROSS
        if not klein.any():
            break
        hx = zx * zx - zy * zy + px
        hy = 2 * zx * zy + py
        zx = np.where(klein, hx, zx)
        zy = np.where(klein, hy, zy)
        schritte += klein
        r2 = zx * zx + zy * zy
    return schritte + 1 - np.log2(0.5 * np.log(r2))


def rechne(cx: np.ndarray, cy: np.ndarray, grenze: int, block: int = BLOCK):
    """Rechenkern. Liefert Abbruchwerte und gebrochene Abbruchwerte.

    cx: Koordinate jeder Spalte, cy: Koordinate jeder Zeile. Beide Ergebnisse
    haben die Form (Spalten, Zeilen). Die Rechenschritte für hx und hy sind
    dieselben wie in MANDELDA.PAS und dürfen nicht umgestellt werden.
    """
    spalten, zeilen = len(cx), len(cy)
    roh = np.full((spalten, zeilen), grenze + 1, np.int32)
    glatt = np.zeros((spalten, zeilen), np.float32)
    for a in range(0, spalten, block):
        b = min(a + block, spalten)
        px = np.repeat(cx[a:b], zeilen)
        py = np.tile(cy, b - a)
        idx = np.arange((b - a) * zeilen)
        zx = np.zeros(idx.size)
        zy = np.zeros(idx.size)
        roh_b = roh[a:b].reshape(-1)
        glatt_b = glatt[a:b].reshape(-1)
        for schritt in range(1, grenze + 2):
            hx = zx * zx - zy * zy + px
            hy = 2 * zx * zy + py
            zx, zy = hx, hy
            r2 = zx * zx + zy * zy
            raus = r2 >= 4
            if raus.any():
                if schritt <= grenze:
                    roh_b[idx[raus]] = schritt
                    glatt_b[idx[raus]] = _gebrochen(
                        zx[raus], zy[raus], px[raus], py[raus], r2[raus], schritt
                    )
                bleibt = ~raus
                idx, px, py = idx[bleibt], px[bleibt], py[bleibt]
                zx, zy = zx[bleibt], zy[bleibt]
                if idx.size == 0:
                    break
    return roh, glatt


# ------------------------------------------------------------ wie 1991 (R1)


def abbruchwerte(
    ausschnitt: Ausschnitt, raster: int = RASTER, grenze: int = ABBRUCHGRENZE
) -> np.ndarray:
    """Abbruchwerte für einen Ausschnitt nach R1, als Feld [Spalte, Zeile].

    Werte 1 bis grenze: Punkt außerhalb der Menge. Wert grenze + 1: Punkt
    der Menge.
    """
    xmin, xmax = float(ausschnitt.xmin), float(ausschnitt.xmax)
    ymin, ymax = float(ausschnitt.ymin), float(ausschnitt.ymax)
    seite_x = (xmax - xmin) / raster
    seite_y = (ymax - ymin) / raster
    nummer = np.arange(1, raster + 1)
    roh, _ = rechne(nummer * seite_x + xmin, nummer * seite_y + ymin, grenze)
    return roh.astype(np.int16 if grenze + 1 <= np.iinfo(np.int16).max else np.int32)


# ------------------------------------------- Mittelpunkt und Bildbreite (R10)


def koordinaten(bild: Bildausschnitt):
    """Koordinaten der Spalten und Zeilen und der Punktabstand (R10, R11)."""
    a = float(bild.breite / bild.pixel_b)
    mx, my = float(bild.mitte_x), float(bild.mitte_y)
    cx = mx + (np.arange(bild.pixel_b) - (bild.pixel_b - 1) / 2) * a
    cy = my - (np.arange(bild.pixel_h) - (bild.pixel_h - 1) / 2) * a
    return cx, cy, a


def pruefe_genauigkeit(bild: Bildausschnitt) -> list[str]:
    """Prüft die Grenze der Rechengenauigkeit (R15). Liefert Warnungen.

    Löst einen Eingabefehler aus, wenn benachbarte Spalten oder Zeilen
    dieselbe Koordinate bekämen.
    """
    cx, cy, a = koordinaten(bild)
    if not (np.diff(cx) > 0).all() or not (np.diff(cy) < 0).all():
        raise Eingabefehler(
            f"Die Bildbreite {dezimaltext(bild.breite)} ist für {bild.pixel_b} x {bild.pixel_h} "
            "Bildpunkte zu klein: Benachbarte Bildpunkte bekämen dieselbe "
            "Koordinate. Tiefer geht es erst mit Stufe 7."
        )
    warnungen = []
    feinheit = max(np.spacing(np.abs(cx).max()), np.spacing(np.abs(cy).max()))
    if float(bild.breite) < WARNGRENZE_BREITE:
        warnungen.append(
            f"Die Bildbreite {dezimaltext(bild.breite)} liegt unter 0.000000000001. Das Bild wird "
            "gerechnet, kann aber ungleichmäßig werden."
        )
    elif a < _FEINHEIT_FAKTOR * feinheit:
        warnungen.append(
            "Der Punktabstand liegt dicht an der Grenze der Rechengenauigkeit. "
            "Die Bildpunkte liegen nicht mehr gleichmäßig."
        )
    return warnungen


def berechne_bild(bild: Bildausschnitt, grenze: int = ABBRUCHGRENZE):
    """Rechnet ein Bild nach R10. Liefert Abbruchwerte, gebrochene Werte, Warnungen."""
    warnungen = pruefe_genauigkeit(bild)
    cx, cy, _ = koordinaten(bild)
    roh, glatt = rechne(cx, cy, grenze)
    return roh, glatt, warnungen
