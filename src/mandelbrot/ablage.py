"""Lauf-Ordner schreiben und lesen (R8)."""

from __future__ import annotations

import json
import re
import shutil
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

from . import __version__
from .typen import ABBRUCHGRENZE, RASTER, Ausschnitt, Bildausschnitt, Eingabefehler, Lauf

AUSGABE = Path("ausgabe")
FORMAT = 2  # Stufe 2a. Format 1 (Stufe 1) wird weiter gelesen.
FORMATE_LESBAR = (1, 2)

DATEI_ROH = "roh.npy"
DATEI_GLATT = "glatt.npy"
DATEI_STUFEN = "stufen.npy"
DATEI_BILD = "bild.png"
DATEI_BESCHREIBUNG = "lauf.json"
DATEI_VERGLEICH = "vergleich.png"


def pruefe_name(name: str) -> str:
    if not name or name in (".", "..") or any(z in name for z in '/\\:*?"<>|'):
        raise Eingabefehler(
            f"Der Name '{name}' ist als Ordnername nicht erlaubt. "
            'Nicht erlaubt sind die Zeichen / \\ : * ? " < > |'
        )
    return name


def beschreibung(
    herkunft: str,
    ausschnitt: Ausschnitt | Bildausschnitt,
    palette: int,
    grenze: int = ABBRUCHGRENZE,
) -> dict:
    """Grundgerüst für lauf.json. Weitere Angaben ergänzt der Aufrufer.

    Ein Ausschnitt nach R1 steht unter "ausschnitt", ein Bild nach R10
    unter "bild".
    """
    angaben = {
        "format": FORMAT,
        "programm": f"ki-mandelbrot {__version__}",
        "erzeugt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "herkunft": herkunft,
    }
    if isinstance(ausschnitt, Bildausschnitt):
        angaben["bild"] = ausschnitt.als_text()
        angaben["raster"] = [ausschnitt.pixel_b, ausschnitt.pixel_h]
    else:
        angaben["ausschnitt"] = ausschnitt.als_text()
        angaben["lage"] = "wie 1991"
        angaben["raster"] = [RASTER, RASTER]
    angaben["abbruchgrenze"] = grenze
    angaben["wert_in_menge"] = grenze + 1
    angaben["palette"] = palette
    return angaben


def schreibe_lauf(
    ordner: str | Path,
    *,
    beschreibung: dict,
    stufen: np.ndarray,
    bild: Image.Image,
    roh: np.ndarray | None = None,
    glatt: np.ndarray | None = None,
    vergleichsbild: Image.Image | None = None,
    ueberschreiben: bool = False,
) -> Path:
    """Legt einen Lauf-Ordner an. Ein vorhandener wird nie stillschweigend ersetzt."""
    ordner = Path(ordner)
    pruefe_name(ordner.name)
    if ordner.exists():
        if not ueberschreiben:
            raise Eingabefehler(
                f"Der Lauf '{ordner.name}' existiert schon. "
                "Mit --ueberschreiben wird er ersetzt, mit --name bekommt der "
                "neue Lauf einen anderen Namen."
            )
        if not ordner.is_dir():
            raise Eingabefehler(f"{ordner} ist kein Ordner und wird nicht ersetzt.")
        shutil.rmtree(ordner)
    ordner.mkdir(parents=True)
    if roh is not None:
        # int16 reicht bis Abbruchgrenze 32.766, darüber int32.
        grenze = beschreibung.get("abbruchgrenze", ABBRUCHGRENZE)
        typ = np.int16 if grenze + 1 <= np.iinfo(np.int16).max else np.int32
        np.save(ordner / DATEI_ROH, roh.astype(typ))
    if glatt is not None:
        np.save(ordner / DATEI_GLATT, glatt.astype(np.float32))
    np.save(ordner / DATEI_STUFEN, stufen.astype(np.int16))
    bild.save(ordner / DATEI_BILD)
    if vergleichsbild is not None:
        vergleichsbild.save(ordner / DATEI_VERGLEICH)
    (ordner / DATEI_BESCHREIBUNG).write_text(_als_json(beschreibung), encoding="utf-8")
    return ordner


def _als_json(inhalt: dict) -> str:
    """JSON mit zwei Leerzeichen Einzug. Zahlenlisten stehen in einer Zeile."""
    text = json.dumps(inhalt, indent=2, ensure_ascii=False)

    def einzeilig(treffer: re.Match) -> str:
        return "[" + ", ".join(treffer.group(1).split()).replace(",,", ",") + "]"

    text = re.sub(r"\[\s*((?:-?\d+(?:\.\d+)?,?\s*)+)\]", einzeilig, text)
    return text + "\n"


def lies_lauf(ordner: str | Path) -> Lauf:
    ordner = Path(ordner)
    datei = ordner / DATEI_BESCHREIBUNG
    if not datei.is_file():
        raise Eingabefehler(
            f"{ordner} ist kein Lauf-Ordner: Die Datei {DATEI_BESCHREIBUNG} fehlt."
        )
    inhalt = json.loads(datei.read_text(encoding="utf-8"))
    if inhalt.get("format") not in FORMATE_LESBAR:
        raise Eingabefehler(
            f"{datei} hat das Format {inhalt.get('format')}, lesbar sind die "
            f"Formate {FORMATE_LESBAR[0]} und {FORMATE_LESBAR[1]}."
        )
    stufen = np.load(ordner / DATEI_STUFEN)

    def lade(name: str):
        datei = ordner / name
        return np.load(datei) if datei.is_file() else None

    return Lauf(
        ordner=ordner,
        beschreibung=inhalt,
        stufen=stufen,
        roh=lade(DATEI_ROH),
        glatt=lade(DATEI_GLATT),
    )


def bild_aus(beschreibung: dict) -> Bildausschnitt:
    b = beschreibung["bild"]
    breite, hoehe = beschreibung["raster"]
    return Bildausschnitt.aus_text(b["mitte_x"], b["mitte_y"], b["breite"], f"{breite}x{hoehe}")


def gegenstand_aus(beschreibung: dict) -> Ausschnitt | Bildausschnitt:
    """Liefert das Bild nach R10 oder den Ausschnitt nach R1, je nach Lauf."""
    if "bild" in beschreibung:
        return bild_aus(beschreibung)
    return ausschnitt_aus(beschreibung)


def ausschnitt_aus(beschreibung: dict) -> Ausschnitt:
    a = beschreibung["ausschnitt"]
    return Ausschnitt.aus_text(a["xmin"], a["xmax"], a["ymin"], a["ymax"])
