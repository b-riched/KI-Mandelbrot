"""Einstellungen aus mandelbrot.toml (R17) und die Ordner der Stufe 3."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .typen import Eingabefehler

DATEI = "mandelbrot.toml"
STAENDE = ("neu", "laeuft", "fertig", "fehler")

_STANDARD = {
    "ordner": {"jobs": "_JOBS", "ergebnisse": "_ERGEBNISSE", "ereignisse": "_EVENTS"},
    "server": {"adresse": "0.0.0.0", "port": 8000},
    "arbeiter": {"pause_sekunden": 2},
}


@dataclass(frozen=True)
class Einstellungen:
    projektordner: Path
    jobs: Path
    ergebnisse: Path
    ereignisse: Path
    adresse: str
    port: int
    pause_sekunden: float

    def ordner_fuer(self, stand: str) -> Path:
        """Der Ordner der Warteschlange für einen Stand, zum Beispiel _JOBS/neu."""
        if stand not in STAENDE:
            raise ValueError(f"unbekannter Stand: {stand}")
        return self.jobs / stand


def lade(projektordner: str | Path | None = None) -> Einstellungen:
    """Liest mandelbrot.toml aus dem Projektordner. Ohne die Datei gelten die Standardwerte."""
    projektordner = Path(projektordner) if projektordner is not None else Path.cwd()
    werte = {abschnitt: dict(inhalt) for abschnitt, inhalt in _STANDARD.items()}
    datei = projektordner / DATEI
    if datei.is_file():
        try:
            gelesen = tomllib.loads(datei.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as fehler:
            raise Eingabefehler(f"{DATEI} ist nicht lesbar: {fehler}") from None
        for abschnitt, inhalt in gelesen.items():
            if abschnitt not in _STANDARD or not isinstance(inhalt, dict):
                raise Eingabefehler(
                    f"{DATEI}: Der Abschnitt [{abschnitt}] ist unbekannt. Möglich sind "
                    + ", ".join(f"[{name}]" for name in _STANDARD)
                )
            for schluessel, wert in inhalt.items():
                if schluessel not in _STANDARD[abschnitt]:
                    raise Eingabefehler(
                        f"{DATEI}: In [{abschnitt}] ist '{schluessel}' unbekannt. Möglich sind "
                        + ", ".join(_STANDARD[abschnitt])
                    )
                werte[abschnitt][schluessel] = wert

    def pfad(schluessel: str) -> Path:
        wert = werte["ordner"][schluessel]
        if not isinstance(wert, str) or not wert:
            raise Eingabefehler(f"{DATEI}: [ordner] {schluessel} muss ein Ordnername sein.")
        return projektordner / wert  # ein Pfad mit Laufwerk ersetzt den Projektordner

    adresse, port = werte["server"]["adresse"], werte["server"]["port"]
    pause = werte["arbeiter"]["pause_sekunden"]
    if not isinstance(adresse, str) or not adresse:
        raise Eingabefehler(f"{DATEI}: [server] adresse muss eine Adresse sein.")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise Eingabefehler(f"{DATEI}: [server] port muss zwischen 1 und 65535 liegen.")
    if isinstance(pause, bool) or not isinstance(pause, (int, float)) or pause <= 0:
        raise Eingabefehler(f"{DATEI}: [arbeiter] pause_sekunden muss größer als 0 sein.")
    return Einstellungen(
        projektordner=projektordner,
        jobs=pfad("jobs"),
        ergebnisse=pfad("ergebnisse"),
        ereignisse=pfad("ereignisse"),
        adresse=adresse,
        port=port,
        pause_sekunden=float(pause),
    )


def lege_ordner_an(einstellungen: Einstellungen) -> None:
    """Legt alle Ordner aus R17 an, soweit sie fehlen."""
    for stand in STAENDE:
        einstellungen.ordner_fuer(stand).mkdir(parents=True, exist_ok=True)
    einstellungen.ergebnisse.mkdir(parents=True, exist_ok=True)
    einstellungen.ereignisse.mkdir(parents=True, exist_ok=True)
