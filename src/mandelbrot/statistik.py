"""Von Abbruchwerten zu Farbstufen (R3), portiert aus MANDELST.PAS."""

from __future__ import annotations

import numpy as np

from .typen import ABBRUCHGRENZE, Eingabefehler

MAX_BEREICHE_STANDARD = 255
MAX_BEREICHE_1991 = 256
_OHNE_HOECHSTZAHL = 10**9


def haeufigkeit(roh: np.ndarray, grenze: int = ABBRUCHGRENZE) -> np.ndarray:
    """Zählt, wie viele Bildpunkte jeden Abbruchwert haben."""
    return np.bincount(roh.ravel(), minlength=grenze + 2)


def pruefe_einstellungen(schwelle: int, max_bereiche: int) -> None:
    if schwelle < 0:
        raise Eingabefehler(f"Die Schwelle darf nicht negativ sein, angegeben: {schwelle}")
    if not 1 <= max_bereiche <= MAX_BEREICHE_1991:
        raise Eingabefehler(
            "Die Höchstzahl der Bereiche muss zwischen 1 und 256 liegen, "
            f"angegeben: {max_bereiche}"
        )


def bereichsbreiten(
    haeufigkeit: np.ndarray,
    schwelle: int,
    max_bereiche: int = MAX_BEREICHE_STANDARD,
    grenze: int = ABBRUCHGRENZE,
) -> list[int]:
    """Fasst die Abbruchwerte 1 bis grenze zu Bereichen zusammen.

    Rückgabe: Breite jedes Bereichs, also die Zahl der Abbruchwerte darin.
    Die Summe ist immer die Abbruchgrenze.

    Ab Schwelle 1 werden nur die Abbruchwerte durchlaufen, die im Bild
    vorkommen. Werte ohne Bildpunkte können nie einen Bereich schließen.
    Das Ergebnis ist dasselbe wie beim Durchlaufen aller Werte.
    """
    if schwelle <= 0:
        breiten = [1] * grenze
    else:
        breiten, anfang, summe = [], 1, 0
        werte = np.flatnonzero(haeufigkeit[1 : grenze + 1]) + 1
        for wert, anzahl in zip(werte.tolist(), haeufigkeit[werte].tolist()):
            summe += anzahl
            if summe >= schwelle:
                breiten.append(wert - anfang + 1)
                anfang, summe = wert + 1, 0
        if anfang <= grenze:
            breiten.append(grenze - anfang + 1)
    if len(breiten) > max_bereiche:
        # Restverteilung wie im Original: von hinten jeweils die Hälfte,
        # halbe Werte aufwärts gerundet.
        breiten = breiten[:max_bereiche]
        rest = grenze - sum(breiten)
        i = max_bereiche - 1
        while rest > 0:
            anteil = rest if i == 0 else (rest + 1) // 2
            breiten[i] += anteil
            rest -= anteil
            i -= 1
    return breiten


def stufentabelle(breiten: list[int]) -> np.ndarray:
    """Tabelle Abbruchwert -> Farbstufe.

    Die Summe der Breiten ist die Abbruchgrenze. Der Wert 0 und der Wert
    der Menge (Abbruchgrenze + 1) ergeben die Farbstufe 0.
    """
    tabelle = np.zeros(sum(breiten) + 2, np.int16)
    wert = 1
    for nummer, breite in enumerate(breiten, start=1):
        tabelle[wert : wert + breite] = nummer
        wert += breite
    return tabelle


def farbstufen(roh: np.ndarray, tabelle: np.ndarray) -> np.ndarray:
    return tabelle[roh]


def automatische_schwelle(
    haeufigkeit: np.ndarray,
    max_bereiche: int = MAX_BEREICHE_STANDARD,
    grenze: int = ABBRUCHGRENZE,
) -> int:
    """Kleinste Schwelle ab 1, bei der höchstens max_bereiche Bereiche entstehen.

    Gesucht wird per Halbierung. Das ist zulässig, weil die Zahl der
    Bereiche mit wachsender Schwelle nie steigt.
    """

    def passt(schwelle: int) -> bool:
        bereiche = bereichsbreiten(haeufigkeit, schwelle, _OHNE_HOECHSTZAHL, grenze)
        return len(bereiche) <= max_bereiche

    if passt(1):
        return 1
    # Oberhalb der Zahl aller Punkte außerhalb der Menge gibt es nur einen Bereich.
    zu_klein, passend = 1, int(haeufigkeit[1 : grenze + 1].sum()) + 1
    while passend - zu_klein > 1:
        mitte = (zu_klein + passend) // 2
        if passt(mitte):
            passend = mitte
        else:
            zu_klein = mitte
    return passend
