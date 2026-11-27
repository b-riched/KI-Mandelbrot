"""Der Arbeiter: arbeitet die Warteschlange ab (R21, R22, R23)."""

from __future__ import annotations

import json
import os
import shutil
import time
import traceback
from datetime import datetime
from pathlib import Path

from . import ablage, berechnen, jobs, protokoll, warteschlange
from .einfaerben import bild as faerbe
from .einstellungen import Einstellungen
from .paletten import palette
from .statistik import bilde_farbstufen
from .typen import Eingabefehler

LEBENSZEICHEN = "arbeiter.json"
LEBENSZEICHEN_GUELTIG = 30.0  # Sekunden


# ------------------------------------------------------------ Lebenszeichen


def schreibe_lebenszeichen(
    einstellungen: Einstellungen, job: str | None, beendet: bool = False
) -> None:
    """Hält fest, ob der Arbeiter läuft und woran er gerade rechnet."""
    einstellungen.jobs.mkdir(parents=True, exist_ok=True)
    datei = einstellungen.jobs / LEBENSZEICHEN
    teil = datei.with_name(datei.name + ".teil")
    inhalt = {"zeit": protokoll.zeittext(protokoll.jetzt()), "job": job, "beendet": beendet}
    teil.write_text(json.dumps(inhalt), encoding="utf-8")
    os.replace(teil, datei)


def lies_lebenszeichen(einstellungen: Einstellungen) -> dict:
    """Liefert {"aktiv": bool, "job": Name oder None, "zeit": Text oder None}."""
    try:
        inhalt = json.loads((einstellungen.jobs / LEBENSZEICHEN).read_text(encoding="utf-8"))
        alter = time.time() - datetime.fromisoformat(inhalt["zeit"]).timestamp()
        job = inhalt.get("job")
    except (OSError, ValueError, KeyError, TypeError):
        return {"aktiv": False, "job": None, "zeit": None}
    if inhalt.get("beendet"):
        return {"aktiv": False, "job": None, "zeit": inhalt["zeit"]}
    return {
        "aktiv": job is not None or alter <= LEBENSZEICHEN_GUELTIG,
        "job": job,
        "zeit": inhalt["zeit"],
    }


# ------------------------------------------------------------------ ein Job


def _scheitere(einstellungen: Einstellungen, name: str, grund: str, spur: str = "") -> None:
    """Legt einen gescheiterten Job mit seinem Grund in 'fehler' ab (R22)."""
    shutil.rmtree(warteschlange.teilordner(einstellungen, name), ignore_errors=True)
    if warteschlange.datei(einstellungen, "laeuft", name).is_file():
        warteschlange.verschiebe(einstellungen, name, "laeuft", "fehler")
    text = grund + ("\n\n" + spur if spur else "") + "\n"
    warteschlange.fehlertext_datei(einstellungen, name).write_text(text, encoding="utf-8")
    protokoll.schreibe(einstellungen, name, "fehler", grund)


def bearbeite(einstellungen: Einstellungen, job_datei: Path) -> bool:
    """Rechnet einen Job aus 'neu'. Rückgabe: True bei Erfolg, False bei Fehler."""
    name = job_datei.stem
    angelegt_fallback = protokoll.zeittext(
        datetime.fromtimestamp(job_datei.stat().st_mtime).astimezone()
    )
    laeuft = warteschlange.verschiebe(einstellungen, name, "neu", "laeuft")
    schreibe_lebenszeichen(einstellungen, name)
    gestartet = protokoll.jetzt()
    try:
        angaben = jobs.lies(laeuft)
        if "angelegt" not in angaben:
            protokoll.schreibe(einstellungen, name, "entdeckt", "als Datei abgelegt")
        protokoll.schreibe(einstellungen, name, "gestartet", zeitpunkt=gestartet)
        job = jobs.pruefe(angaben, name, einstellungen)
        ziel = einstellungen.ergebnisse / name
        if ziel.exists():
            raise Eingabefehler(
                f"Zu dem Jobnamen '{name}' gibt es schon ein Ergebnis. "
                "Ein vorhandenes Ergebnis wird nicht überschrieben."
            )

        beginn = time.perf_counter()
        roh, glatt, warnungen = berechnen.berechne_bild(job.bild, job.abbruchgrenze)
        stufen, statistik = bilde_farbstufen(
            roh, job.schwelle, job.max_bereiche, job.abbruchgrenze
        )
        fertig = protokoll.jetzt()
        dauer = round(time.perf_counter() - beginn, 1)

        angaben_lauf = ablage.beschreibung("berechnet", job.bild, job.palette, job.abbruchgrenze)
        angaben_lauf["statistik"] = statistik
        angaben_lauf["job"] = {
            "name": name,
            "elternbild": job.elternbild,
            "serie": job.serie,
            "notiz": job.notiz,
            "angelegt": job.angelegt or angelegt_fallback,
            "gestartet": protokoll.zeittext(gestartet),
            "fertig": protokoll.zeittext(fertig),
            "rechenzeit_sekunden": dauer,
            "warnungen": warnungen,
        }
        # Erst vollständig unter einem vorläufigen Namen schreiben, dann
        # umbenennen. So ist nie ein halbes Ergebnis sichtbar (R21).
        teil = warteschlange.teilordner(einstellungen, name)
        ablage.schreibe_lauf(
            teil,
            beschreibung=angaben_lauf,
            stufen=stufen,
            bild=faerbe(stufen, palette(job.palette)),
            roh=roh,
            glatt=glatt,
            ueberschreiben=True,
        )
        os.replace(teil, ziel)
        warteschlange.verschiebe(einstellungen, name, "laeuft", "fertig")
        for warnung in warnungen:
            protokoll.schreibe(einstellungen, name, "warnung", warnung)
        protokoll.schreibe(
            einstellungen,
            name,
            "fertig",
            f"{dauer} s, {job.bild.pixel_b} x {job.bild.pixel_h}, Abbruchgrenze {job.abbruchgrenze}",
        )
        return True
    except Eingabefehler as fehler:
        _scheitere(einstellungen, name, str(fehler))
        return False
    except Exception as fehler:  # Der Arbeiter soll nach jedem Fehler weiterlaufen.
        _scheitere(
            einstellungen,
            name,
            f"Unerwarteter Fehler: {type(fehler).__name__}: {fehler}",
            traceback.format_exc(),
        )
        return False
    # Strg+C (KeyboardInterrupt) wird nicht abgefangen: Der Job bleibt in
    # 'laeuft' und wird beim nächsten Start neu gerechnet (R23).


# -------------------------------------------------------------- die Schleife


def arbeite(
    einstellungen: Einstellungen,
    einmal: bool = False,
    soll_enden=lambda: False,
    mindestalter: float = warteschlange.MINDESTALTER,
) -> int:
    """Arbeitet die Warteschlange ab. Rückgabe: Zahl der bearbeiteten Jobs.

    einmal=True: endet, sobald kein Job mehr wartet.
    """
    for name in warteschlange.raeume_auf(einstellungen):
        print(f"Zurückgestellt nach Neustart: {name}")
    protokoll.schreibe(einstellungen, protokoll.OHNE_JOB, "arbeiter gestartet")
    bearbeitet = 0
    try:
        while not soll_enden():
            job_datei = warteschlange.naechster(einstellungen, mindestalter)
            if job_datei is None:
                if einmal:
                    break
                schreibe_lebenszeichen(einstellungen, None)
                time.sleep(einstellungen.pause_sekunden)
                continue
            print(f"Rechne {job_datei.stem} ...", flush=True)
            erfolg = bearbeite(einstellungen, job_datei)
            print(f"  {'fertig' if erfolg else 'gescheitert'}: {job_datei.stem}", flush=True)
            bearbeitet += 1
    finally:
        schreibe_lebenszeichen(einstellungen, None, beendet=True)
        protokoll.schreibe(einstellungen, protokoll.OHNE_JOB, "arbeiter beendet")
    return bearbeitet
