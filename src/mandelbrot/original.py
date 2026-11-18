"""Lesen der Originaldateien von 1991 (R6)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import numpy as np

from .typen import RASTER, Ausschnitt, Eingabefehler

DATEIGROESSE = (RASTER + 1) * RASTER * 2  # 461.760 Bytes


@dataclass(frozen=True)
class Leseregel:
    """Eine Zeile der Lesetabelle."""

    faktor: int
    nachrechnung: tuple[str, str, str, str]  # xmin, xmax, ymin, ymax
    schwelle_1991: int
    grenze_menge: float  # Abnahmekriterium A2
    grenze_stufen: float | None  # Abnahmekriterium A3, None: keine Grenze


LESETABELLE: dict[str, Leseregel] = {
    "M0.DAT": Leseregel(1000, ("-2.1", "0.6", "-1.35", "1.35"), 4, 0.999, 0.995),
    "M01.DAT": Leseregel(1000, ("-0.3", "0", "-0.9", "-0.6"), 38, 0.999, 0.990),
    "M1.DAT": Leseregel(1000, ("-0.429", "0.201", "-1.215", "-0.585"), 14, 0.999, 0.990),
    "M11.DAT": Leseregel(
        1000, ("-0.2175", "-0.1235", "-0.7317", "-0.6378"), 52, 0.990, None
    ),
    "M12.DAT": Leseregel(
        10000, ("-0.1443", "-0.0504", "-1.0008", "-0.9063"), 0, 0.999, None
    ),
}


@dataclass(frozen=True)
class OriginalBild:
    name: str  # Dateiname in Großbuchstaben, zum Beispiel "M0.DAT"
    stufen: np.ndarray  # Farbstufen, Feld [Spalte, Zeile]
    faktor: int
    kopfzeile: Ausschnitt  # Koordinaten, wie sie in der Datei stehen
    nachrechnung: Ausschnitt  # Koordinaten für die Nachrechnung
    regel: Leseregel | None  # None, wenn die Datei nicht in der Lesetabelle steht


def lies_dat(pfad: str | Path, faktor: int | None = None) -> OriginalBild:
    """Liest eine .DAT-Datei im Format von 1991."""
    pfad = Path(pfad)
    if not pfad.is_file():
        raise Eingabefehler(f"Die Datei gibt es nicht: {pfad}")
    groesse = pfad.stat().st_size
    if groesse != DATEIGROESSE:
        raise Eingabefehler(
            f"{pfad.name} hat {groesse} Bytes, erwartet sind {DATEIGROESSE}. "
            "Das ist keine Datei im Format von 1991."
        )
    name = pfad.name.upper()
    regel = LESETABELLE.get(name)
    if regel is not None and faktor is not None:
        # Korrektur F-01 aus der Abnahme von Stufe 1: Der Faktor einer Datei
        # der Lesetabelle steht fest und lässt sich nicht überschreiben.
        raise Eingabefehler(
            f"{pfad.name} steht in der Lesetabelle, der Faktor {regel.faktor} ist fest. "
            "Die Angabe --faktor gilt nur für Dateien, die nicht in der Lesetabelle stehen."
        )
    if faktor is None:
        if regel is None:
            raise Eingabefehler(
                f"{pfad.name} steht nicht in der Lesetabelle. "
                "Bitte den Faktor mit --faktor angeben, zum Beispiel 1000."
            )
        faktor = regel.faktor
    if faktor <= 0:
        raise Eingabefehler(f"Der Faktor muss größer als 0 sein, angegeben: {faktor}")

    daten = np.fromfile(pfad, dtype="<i2").reshape(RASTER + 1, RASTER)
    kopf = daten[0]
    # Belegt sind nur die Felder 1, 3, 5 und 7. Der Rest ist nicht
    # initialisierter Speicher von 1991.
    xmin, xmax, ymin, ymax = (
        Decimal(int(kopf[feld])) / Decimal(faktor) for feld in (0, 2, 4, 6)
    )
    kopfzeile = Ausschnitt(xmin, xmax, ymin, ymax)
    if regel is not None and faktor == regel.faktor:
        nachrechnung = Ausschnitt.aus_text(*regel.nachrechnung)
    else:
        nachrechnung = kopfzeile
    return OriginalBild(
        name=name,
        stufen=daten[1:].copy(),
        faktor=faktor,
        kopfzeile=kopfzeile,
        nachrechnung=nachrechnung,
        regel=regel,
    )
