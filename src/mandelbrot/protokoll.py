"""Das Protokoll in _EVENTS (R25): eine Textdatei pro Tag, eine Zeile pro Ereignis."""

from __future__ import annotations

from datetime import datetime

from .einstellungen import Einstellungen

OHNE_JOB = "-"


def jetzt() -> datetime:
    return datetime.now().astimezone()


def zeittext(zeitpunkt: datetime) -> str:
    return zeitpunkt.isoformat(timespec="seconds")


def schreibe(
    einstellungen: Einstellungen,
    job: str,
    ereignis: str,
    text: str = "",
    zeitpunkt: datetime | None = None,
) -> None:
    """Hängt eine Zeile an: Zeitpunkt, Jobname oder '-', Ereignis, Text, durch Tabulatoren getrennt."""
    zeitpunkt = zeitpunkt or jetzt()
    einstellungen.ereignisse.mkdir(parents=True, exist_ok=True)
    datei = einstellungen.ereignisse / f"{zeitpunkt:%Y-%m-%d}.log"
    einzeilig = " ".join(str(text).split())
    zeile = "\t".join((zeittext(zeitpunkt), job or OHNE_JOB, ereignis, einzeilig))
    with datei.open("a", encoding="utf-8", newline="\n") as ausgabe:
        ausgabe.write(zeile + "\n")
