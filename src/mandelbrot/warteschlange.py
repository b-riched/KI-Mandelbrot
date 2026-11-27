"""Die Warteschlange in _JOBS (R17, R20, R23).

Ein Job wechselt den Stand, indem seine Datei in den Nachbarordner
umbenannt wird.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path

from . import protokoll
from .einstellungen import STAENDE, Einstellungen, lege_ordner_an

ENDUNG = ".json"
TEIL = ".teil"
MINDESTALTER = 2.0  # Sekunden, die eine neue Datei liegen bleibt (R20)


def datei(einstellungen: Einstellungen, stand: str, name: str) -> Path:
    return einstellungen.ordner_fuer(stand) / f"{name}{ENDUNG}"


def fehlertext_datei(einstellungen: Einstellungen, name: str) -> Path:
    return einstellungen.ordner_fuer("fehler") / f"{name}.fehler.txt"


def teilordner(einstellungen: Einstellungen, name: str) -> Path:
    """Hier entsteht ein Ergebnis, bevor es vollständig ist (R21)."""
    return einstellungen.ergebnisse / f"{name}{TEIL}"


def angelegt_am(job_datei: Path) -> float:
    """Zeitpunkt, zu dem ein Job angelegt wurde, als Sekunden seit 1970.

    Maßgeblich ist die Angabe 'angelegt' in der Datei, ersatzweise das
    Änderungsdatum der Datei.
    """
    try:
        angaben = json.loads(job_datei.read_text(encoding="utf-8-sig"))
        return datetime.fromisoformat(angaben["angelegt"]).timestamp()
    except (OSError, ValueError, KeyError, TypeError):
        return job_datei.stat().st_mtime


def jobs_im_stand(einstellungen: Einstellungen, stand: str) -> list[Path]:
    ordner = einstellungen.ordner_fuer(stand)
    if not ordner.is_dir():
        return []
    return sorted(p for p in ordner.iterdir() if p.is_file() and p.suffix == ENDUNG)


def naechster(einstellungen: Einstellungen, mindestalter: float = MINDESTALTER) -> Path | None:
    """Der älteste Job aus 'neu', oder None, wenn keiner wartet (R20)."""
    grenze = time.time() - mindestalter
    wartend = [p for p in jobs_im_stand(einstellungen, "neu") if p.stat().st_mtime <= grenze]
    if not wartend:
        return None
    return min(wartend, key=lambda p: (angelegt_am(p), p.name))


def verschiebe(einstellungen: Einstellungen, name: str, von: str, nach: str) -> Path:
    ziel = datei(einstellungen, nach, name)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    os.replace(datei(einstellungen, von, name), ziel)
    return ziel


def stand_von(einstellungen: Einstellungen, name: str) -> str | None:
    for stand in STAENDE:
        if datei(einstellungen, stand, name).is_file():
            return stand
    return None


def name_vergeben(einstellungen: Einstellungen, name: str) -> bool:
    """Ein Jobname ist vergeben, wenn es einen Job oder ein Ergebnis dieses Namens gibt."""
    return stand_von(einstellungen, name) is not None or (einstellungen.ergebnisse / name).exists()


def raeume_auf(einstellungen: Einstellungen) -> list[str]:
    """Stellt nach einem Neustart unterbrochene Jobs zurück (R23).

    Jobs aus 'laeuft' wandern zurück nach 'neu', halbe Ergebnisse werden
    gelöscht. Rückgabe: die Namen der zurückgestellten Jobs.
    """
    lege_ordner_an(einstellungen)
    zurueck = []
    for job_datei in jobs_im_stand(einstellungen, "laeuft"):
        name = job_datei.stem
        verschiebe(einstellungen, name, "laeuft", "neu")
        protokoll.schreibe(einstellungen, name, "zurueckgestellt", "nach Neustart")
        zurueck.append(name)
    for ordner in einstellungen.ergebnisse.iterdir():
        if ordner.is_dir() and ordner.name.endswith(TEIL):
            shutil.rmtree(ordner)
    return zurueck
