"""Gemeinsame Typen und Konstanten."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

import numpy as np

RASTER = 480
ABBRUCHGRENZE = 1005
WERT_IN_MENGE = 1006

# Stufe 2a: benannte Bildgrößen und Grenzen für Eingaben (R9, R12)
GROESSEN = {
    "hd": (1280, 720),
    "fullhd": (1920, 1080),
    "wqhd": (2560, 1440),
    "ipad": (2360, 1640),
}
SEITE_MIN, SEITE_MAX = 16, 10_000
GRENZE_MIN, GRENZE_MAX = 10, 1_000_000


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


def lies_groesse(text: str) -> tuple[int, int]:
    """Liest eine Bildgröße: einen Namen aus GROESSEN oder BREITExHÖHE (R9)."""
    roh = str(text).strip().lower().replace("×", "x")
    if roh in GROESSEN:
        return GROESSEN[roh]
    treffer = re.fullmatch(r"(\d+)\s*x\s*(\d+)", roh)
    if not treffer:
        raise Eingabefehler(
            f"Die Bildgröße '{text}' ist unbekannt. Möglich sind "
            + ", ".join(GROESSEN)
            + " oder eine Angabe wie 800x600."
        )
    breite, hoehe = int(treffer.group(1)), int(treffer.group(2))
    for name, seite in (("Breite", breite), ("Höhe", hoehe)):
        if not SEITE_MIN <= seite <= SEITE_MAX:
            raise Eingabefehler(
                f"Die {name} des Bildes muss zwischen {SEITE_MIN} und {SEITE_MAX} "
                f"Bildpunkten liegen, angegeben: {seite}"
            )
    return breite, hoehe


def pruefe_abbruchgrenze(grenze: int) -> int:
    if not GRENZE_MIN <= grenze <= GRENZE_MAX:
        raise Eingabefehler(
            f"Die Abbruchgrenze muss zwischen {GRENZE_MIN} und {GRENZE_MAX} liegen, "
            f"angegeben: {grenze}"
        )
    return grenze


@dataclass(frozen=True)
class Bildausschnitt:
    """Ein Bild, beschrieben durch Mittelpunkt, Bildbreite und Bildgröße (R10)."""

    mitte_x: Decimal
    mitte_y: Decimal
    breite: Decimal  # Bildbreite in der Zahlenebene, größer als 0
    pixel_b: int  # Breite in Bildpunkten
    pixel_h: int  # Höhe in Bildpunkten

    @classmethod
    def aus_text(cls, mitte_x: str, mitte_y: str, breite: str, groesse: str) -> Bildausschnitt:
        pixel_b, pixel_h = lies_groesse(groesse)
        bild = cls(
            dezimal(mitte_x, "Der Mittelpunkt x"),
            dezimal(mitte_y, "Der Mittelpunkt y"),
            dezimal(breite, "Die Bildbreite"),
            pixel_b,
            pixel_h,
        )
        if not bild.breite > 0:
            raise Eingabefehler(f"Die Bildbreite muss größer als 0 sein, angegeben: {breite}")
        return bild

    def als_text(self) -> dict[str, str]:
        return {
            "mitte_x": dezimaltext(self.mitte_x),
            "mitte_y": dezimaltext(self.mitte_y),
            "breite": dezimaltext(self.breite),
            "lage": "aufrecht",
        }


@dataclass(frozen=True)
class Lauf:
    """Ein gelesener Lauf-Ordner (R8, R16)."""

    ordner: Path
    beschreibung: dict
    stufen: np.ndarray
    roh: np.ndarray | None
    glatt: np.ndarray | None = None
