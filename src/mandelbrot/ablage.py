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
from .typen import ABBRUCHGRENZE, RASTER, WERT_IN_MENGE, Ausschnitt, Eingabefehler, Lauf

AUSGABE = Path("ausgabe")
FORMAT = 1

DATEI_ROH = "roh.npy"
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


def beschreibung(herkunft: str, ausschnitt: Ausschnitt, palette: int) -> dict:
    """Grundgerüst für lauf.json. Weitere Angaben ergänzt der Aufrufer."""
    return {
        "format": FORMAT,
        "programm": f"ki-mandelbrot {__version__}",
        "erzeugt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "herkunft": herkunft,
        "ausschnitt": ausschnitt.als_text(),
        "raster": [RASTER, RASTER],
        "abbruchgrenze": ABBRUCHGRENZE,
        "wert_in_menge": WERT_IN_MENGE,
        "palette": palette,
    }


def schreibe_lauf(
    ordner: str | Path,
    *,
    beschreibung: dict,
    stufen: np.ndarray,
    bild: Image.Image,
    roh: np.ndarray | None = None,
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
        np.save(ordner / DATEI_ROH, roh.astype(np.int16))
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
    if inhalt.get("format") != FORMAT:
        raise Eingabefehler(
            f"{datei} hat das Format {inhalt.get('format')}, erwartet ist {FORMAT}."
        )
    stufen = np.load(ordner / DATEI_STUFEN)
    roh_datei = ordner / DATEI_ROH
    roh = np.load(roh_datei) if roh_datei.is_file() else None
    return Lauf(ordner=ordner, beschreibung=inhalt, stufen=stufen, roh=roh)


def ausschnitt_aus(beschreibung: dict) -> Ausschnitt:
    a = beschreibung["ausschnitt"]
    return Ausschnitt.aus_text(a["xmin"], a["xmax"], a["ymin"], a["ymax"])
