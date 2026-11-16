"""Autostart unter Windows (R26).

Angeschaltet liegt eine Datei im Autostart-Ordner des angemeldeten
Benutzers. Sie startet beim Anmelden Arbeiter und Job-Server.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from .typen import Eingabefehler

DATEINAME = "KI-Mandelbrot.cmd"
_UNTERORDNER = ("Microsoft", "Windows", "Start Menu", "Programs", "Startup")


def datei(umgebung=None, system: str | None = None) -> Path:
    """Pfad der Autostart-Datei. Löst einen Eingabefehler aus, wenn es keinen Autostart gibt."""
    umgebung = os.environ if umgebung is None else umgebung
    system = sys.platform if system is None else system
    if not system.startswith("win"):
        raise Eingabefehler("Den Autostart gibt es nur unter Windows.")
    appdata = umgebung.get("APPDATA")
    if not appdata:
        raise Eingabefehler("Die Umgebungsvariable APPDATA fehlt. Ohne sie ist der Autostart-Ordner unbekannt.")
    return Path(appdata).joinpath(*_UNTERORDNER) / DATEINAME


def ist_an(umgebung=None, system: str | None = None) -> bool:
    return datei(umgebung, system).is_file()


def inhalt(projektordner: str | Path, python: str | Path) -> str:
    """Der Text der Autostart-Datei.

    Sie wartet, bis der Projektordner erreichbar ist. Ein Netzlaufwerk ist
    beim Anmelden manchmal noch nicht verbunden.
    """
    zeilen = [
        "@echo off",
        "rem KI-Mandelbrot: startet Arbeiter und Job-Server beim Anmelden.",
        'rem Angelegt mit "python -m mandelbrot autostart an",',
        'rem entfernt mit "python -m mandelbrot autostart aus".',
        "chcp 65001 >nul",
        ":warten",
        f'if not exist "{projektordner}\\" (',
        "  timeout /t 5 /nobreak >nul",
        "  goto warten",
        ")",
        f'cd /d "{projektordner}"',
        f'"{python}" -m mandelbrot start',
    ]
    return "\r\n".join(zeilen) + "\r\n"


def schalte_an(
    projektordner: str | Path,
    python: str | Path | None = None,
    umgebung=None,
    system: str | None = None,
) -> Path:
    ziel = datei(umgebung, system)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    text = inhalt(projektordner, python or sys.executable)
    ziel.write_bytes(text.encode("utf-8"))
    return ziel


def schalte_aus(umgebung=None, system: str | None = None) -> bool:
    """Entfernt die Autostart-Datei. Rückgabe: True, wenn es eine gab."""
    ziel = datei(umgebung, system)
    if ziel.is_file():
        ziel.unlink()
        return True
    return False
