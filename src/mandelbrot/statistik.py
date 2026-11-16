"""Von Abbruchwerten zu Farbstufen (R3), portiert aus MANDELST.PAS."""

from __future__ import annotations

import numpy as np

from .typen import ABBRUCHGRENZE, WERT_IN_MENGE, Eingabefehler

MAX_BEREICHE_STANDARD = 255
MAX_BEREICHE_1991 = 256
_OHNE_HOECHSTZAHL = 10**6


def haeufigkeit(roh: np.ndarray) -> np.ndarray:
    """Zählt, wie viele Bildpunkte jeden Abbruchwert haben."""
    return np.bincount(roh.ravel(), minlength=WERT_IN_MENGE + 1)


def pruefe_einstellungen(schwelle: int, max_bereiche: int) -> None:
    if schwelle < 0:
        raise Eingabefehler(f"Die Schwelle darf nicht negativ sein, angegeben: {schwelle}")
    if not 1 <= max_bereiche <= MAX_BEREICHE_1991:
        raise Eingabefehler(
            "Die Höchstzahl der Bereiche muss zwischen 1 und 256 liegen, "
            f"angegeben: {max_bereiche}"
        )


def bereichsbreiten(
    haeufigkeit: np.ndarray, schwelle: int, max_bereiche: int = MAX_BEREICHE_STANDARD
) -> list[int]:
    """Fasst die Abbruchwerte 1 bis 1005 zu Bereichen zusammen.

    Rückgabe: Breite jedes Bereichs, also die Zahl der Abbruchwerte darin.
    Die Summe ist immer 1005.
    """
    breiten, summe = [0], 0
    for wert in range(1, ABBRUCHGRENZE + 1):
        summe += int(haeufigkeit[wert])
        breiten[-1] += 1
        if summe >= schwelle or wert == ABBRUCHGRENZE:
            breiten.append(0)
            summe = 0
    breiten.pop()
    if len(breiten) > max_bereiche:
        # Restverteilung wie im Original: von hinten jeweils die Hälfte,
        # halbe Werte aufwärts gerundet.
        breiten = breiten[:max_bereiche]
        rest = ABBRUCHGRENZE - sum(breiten)
        i = max_bereiche - 1
        while rest > 0:
            anteil = rest if i == 0 else (rest + 1) // 2
            breiten[i] += anteil
            rest -= anteil
            i -= 1
    return breiten


def stufentabelle(breiten: list[int]) -> np.ndarray:
    """Tabelle Abbruchwert -> Farbstufe. Die Werte 0 und 1006 ergeben 0."""
    tabelle = np.zeros(WERT_IN_MENGE + 1, np.int16)
    wert = 1
    for nummer, breite in enumerate(breiten, start=1):
        tabelle[wert : wert + breite] = nummer
        wert += breite
    return tabelle


def farbstufen(roh: np.ndarray, tabelle: np.ndarray) -> np.ndarray:
    return tabelle[roh]


def automatische_schwelle(
    haeufigkeit: np.ndarray, max_bereiche: int = MAX_BEREICHE_STANDARD
) -> int:
    """Kleinste Schwelle ab 1, bei der höchstens max_bereiche Bereiche entstehen."""
    schwelle = 1
    while len(bereichsbreiten(haeufigkeit, schwelle, _OHNE_HOECHSTZAHL)) > max_bereiche:
        schwelle += 1
    return schwelle
