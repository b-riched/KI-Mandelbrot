"""Gemeinsame Typen und Konstanten."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np

RASTER = 480
ABBRUCHGRENZE = 1005
WERT_IN_MENGE = 1006


class Eingabefehler(ValueError):
    """Eine Eingabe ist falsch. Die Meldung ist für den Bildschirm gedacht."""


def dezimal(text: str, name: str) -> Decimal:
    """Liest eine Dezimalzahl mit Punkt oder Komma, ohne zu runden."""
    roh = str(text).strip().replace(",", ".")
    try:
        zahl = Decimal(roh)
    except InvalidOperation:
        raise Eingabefehler(f"{name} ist keine Zahl: '{text}'") from None
    if not zahl.is_finite():
        raise Eingabefehler(f"{name} ist keine endliche Zahl: '{text}'")
    return zahl


def dezimaltext(zahl: Decimal) -> str:
    """Schreibt eine Dezimalzahl mit allen Stellen und ohne Exponent."""
    return format(zahl, "f")


@dataclass(frozen=True)
class Ausschnitt:
    """Das Rechteck der Zahlenebene, das berechnet wird (R1)."""

    xmin: Decimal
    xmax: Decimal
    ymin: Decimal
    ymax: Decimal

    @classmethod
    def aus_text(cls, xmin: str, xmax: str, ymin: str, ymax: str) -> Ausschnitt:
        ausschnitt = cls(
            dezimal(xmin, "xmin"),
            dezimal(xmax, "xmax"),
            dezimal(ymin, "ymin"),
            dezimal(ymax, "ymax"),
        )
        if not ausschnitt.xmin < ausschnitt.xmax:
            raise Eingabefehler(
                f"xmin muss kleiner sein als xmax, angegeben: {xmin} und {xmax}"
            )
        if not ausschnitt.ymin < ausschnitt.ymax:
            raise Eingabefehler(
                f"ymin muss kleiner sein als ymax, angegeben: {ymin} und {ymax}"
            )
        return ausschnitt

    def als_text(self) -> dict[str, str]:
        return {
            "xmin": dezimaltext(self.xmin),
            "xmax": dezimaltext(self.xmax),
            "ymin": dezimaltext(self.ymin),
            "ymax": dezimaltext(self.ymax),
        }


@dataclass(frozen=True)
class Lauf:
    """Ein gelesener Lauf-Ordner (R8)."""

    ordner: Path
    beschreibung: dict
    stufen: np.ndarray
    roh: np.ndarray | None
