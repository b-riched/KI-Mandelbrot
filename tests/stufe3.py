"""Hilfen für die Tests der Stufe 3: ein Projektordner mit Warteschlange im temporären Ordner."""

import json
import os
import time

from mandelbrot import einstellungen as einstellungen_modul

KLEIN = {"mitte_x": "-0.75", "mitte_y": "0", "breite": "3.5", "groesse": "48x32"}


def projekt(ordner):
    """Einstellungen für einen leeren Projektordner, alle Ordner sind angelegt."""
    werte = einstellungen_modul.lade(ordner)
    einstellungen_modul.lege_ordner_an(werte)
    return werte


def lege_job(werte, name, angaben=None, alter=10.0, stand="neu", roh=None):
    """Legt eine Job-Datei ab, als wäre sie vor `alter` Sekunden von Hand kopiert worden."""
    datei = werte.ordner_fuer(stand) / f"{name}.json"
    text = roh if roh is not None else json.dumps(KLEIN if angaben is None else angaben)
    datei.write_text(text, encoding="utf-8")
    zeit = time.time() - alter
    os.utime(datei, (zeit, zeit))
    return datei


def lege_ergebnis(werte, name, raster=(64, 48)):
    """Ein Ergebnisordner, der nur das enthält, was die Prüfung eines Jobs liest."""
    ordner = werte.ergebnisse / name
    ordner.mkdir(parents=True)
    (ordner / "lauf.json").write_text(
        json.dumps({"format": 2, "raster": list(raster)}), encoding="utf-8"
    )
    return ordner


def protokollzeilen(werte):
    zeilen = []
    for datei in sorted(werte.ereignisse.glob("*.log")):
        zeilen += [zeile.split("\t") for zeile in datei.read_text(encoding="utf-8").splitlines()]
    return zeilen


def ereignisse(werte, job):
    return [zeile[2] for zeile in protokollzeilen(werte) if zeile[1] == job]
