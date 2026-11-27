"""Job-Dateien lesen, prüfen und schreiben (R18, R19)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

from . import ablage, berechnen
from .einstellungen import Einstellungen
from .paletten import ANZAHL_PALETTEN
from .statistik import MAX_BEREICHE_STANDARD, pruefe_einstellungen
from .typen import ABBRUCHGRENZE, Bildausschnitt, Eingabefehler, pruefe_abbruchgrenze

PALETTE_STANDARD = 1
PFLICHT = ("mitte_x", "mitte_y", "breite")
FELDER = (
    *PFLICHT,
    "groesse",
    "abbruchgrenze",
    "palette",
    "schwelle",
    "max_bereiche",
    "elternbild",
    "serie",
    "notiz",
    "angelegt",  # ergänzt der Job-Server beim Anlegen
)


@dataclass(frozen=True)
class Job:
    """Ein geprüfter Job."""

    name: str
    bild: Bildausschnitt
    abbruchgrenze: int
    palette: int
    schwelle: int | str  # ganze Zahl ab 0 oder "auto"
    max_bereiche: int
    elternbild: str | None
    serie: str | None
    notiz: str
    angelegt: str | None


def lies(datei: Path) -> dict:
    """Liest eine Job-Datei. Der Inhalt ist danach noch ungeprüft."""
    try:
        angaben = json.loads(Path(datei).read_text(encoding="utf-8-sig"))
    except (json.JSONDecodeError, UnicodeDecodeError) as fehler:
        raise Eingabefehler(f"Die Job-Datei ist kein gültiges JSON: {fehler}") from None
    if not isinstance(angaben, dict):
        raise Eingabefehler("Die Job-Datei muss mit { beginnen und Angaben mit Namen enthalten.")
    return angaben


def schreibe(datei: Path, angaben: dict) -> None:
    """Schreibt eine Job-Datei in einem Schritt, damit niemand eine halbe Datei sieht."""
    datei = Path(datei)
    datei.parent.mkdir(parents=True, exist_ok=True)
    teil = datei.with_name(datei.name + ".teil")
    teil.write_text(json.dumps(angaben, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(teil, datei)


def _ganze_zahl(angaben: dict, feld: str, standard: int) -> int:
    wert = angaben.get(feld, standard)
    if isinstance(wert, bool) or not isinstance(wert, int):
        raise Eingabefehler(f"'{feld}' muss eine ganze Zahl sein, angegeben: {wert!r}")
    return wert


def _text(angaben: dict, feld: str) -> str | None:
    wert = angaben.get(feld)
    if wert is None:
        return None
    if not isinstance(wert, str):
        raise Eingabefehler(f"'{feld}' muss ein Text in Anführungszeichen sein, angegeben: {wert!r}")
    return wert


def _groesse_des_elternbildes(elternbild: str, einstellungen: Einstellungen) -> str:
    ablage.pruefe_name(elternbild)
    ordner = einstellungen.ergebnisse / elternbild
    if not (ordner / ablage.DATEI_BESCHREIBUNG).is_file():
        raise Eingabefehler(f"Das Elternbild '{elternbild}' gibt es nicht unter den Ergebnissen.")
    beschreibung = json.loads((ordner / ablage.DATEI_BESCHREIBUNG).read_text(encoding="utf-8"))
    breite, hoehe = beschreibung["raster"]
    return f"{breite}x{hoehe}"


def pruefe(angaben: dict, name: str, einstellungen: Einstellungen) -> Job:
    """Wendet R18, R19 und R15 an. Fehler sind Eingabefehler mit deutschem Text."""
    ablage.pruefe_name(name)
    unbekannt = sorted(feld for feld in angaben if feld not in FELDER)
    if unbekannt:
        raise Eingabefehler(
            "Unbekannte Angabe im Job: " + ", ".join(unbekannt) + ". Möglich sind "
            + ", ".join(feld for feld in FELDER if feld != "angelegt")
        )
    fehlend = [feld for feld in PFLICHT if feld not in angaben]
    if fehlend:
        raise Eingabefehler("Im Job fehlt: " + ", ".join(fehlend))
    for feld in PFLICHT:
        if not isinstance(angaben[feld], str):
            raise Eingabefehler(
                f"'{feld}' muss als Text in Anführungszeichen stehen, zum Beispiel "
                f'"{feld}": "-0.75". Sonst gehen Nachkommastellen verloren. '
                f"Angegeben: {angaben[feld]!r}"
            )

    elternbild = _text(angaben, "elternbild") or None
    groesse = _text(angaben, "groesse")
    if elternbild is not None:
        groesse_eltern = _groesse_des_elternbildes(elternbild, einstellungen)
        groesse = groesse or groesse_eltern
    if not groesse:
        raise Eingabefehler(
            "Im Job fehlt die Bildgröße ('groesse'). Ohne Angabe gilt die Größe des "
            "Elternbildes, dieser Job hat aber keines."
        )
    bild = Bildausschnitt.aus_text(
        angaben["mitte_x"], angaben["mitte_y"], angaben["breite"], groesse
    )
    berechnen.pruefe_genauigkeit(bild)

    abbruchgrenze = pruefe_abbruchgrenze(_ganze_zahl(angaben, "abbruchgrenze", ABBRUCHGRENZE))
    palette = _ganze_zahl(angaben, "palette", PALETTE_STANDARD)
    if not 0 <= palette < ANZAHL_PALETTEN:
        raise Eingabefehler(f"'palette' muss 0, 1, 2 oder 3 sein, angegeben: {palette}")
    max_bereiche = _ganze_zahl(angaben, "max_bereiche", MAX_BEREICHE_STANDARD)
    schwelle = angaben.get("schwelle", "auto")
    if isinstance(schwelle, str) and schwelle.strip().lower() == "auto":
        schwelle = "auto"
        pruefe_einstellungen(0, max_bereiche)
    elif isinstance(schwelle, bool) or not isinstance(schwelle, int):
        raise Eingabefehler(
            f"'schwelle' muss eine ganze Zahl ab 0 oder \"auto\" sein, angegeben: {schwelle!r}"
        )
    else:
        pruefe_einstellungen(schwelle, max_bereiche)

    return Job(
        name=name,
        bild=bild,
        abbruchgrenze=abbruchgrenze,
        palette=palette,
        schwelle=schwelle,
        max_bereiche=max_bereiche,
        elternbild=elternbild,
        serie=_text(angaben, "serie") or None,
        notiz=_text(angaben, "notiz") or "",
        angelegt=_text(angaben, "angelegt"),
    )
