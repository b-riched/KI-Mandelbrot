"""Der Job-Server (R24): Jobs anlegen, Stand abfragen, Ergebnisse abrufen.

Der Job-Server rechnet nicht selbst. Er schreibt nur in _JOBS/neu und ins
Protokoll, alles andere liest er nur. Nur dieses Modul braucht fastapi.
"""

from __future__ import annotations

import json
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi import Body, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from starlette.exceptions import HTTPException

from . import __version__, ablage, arbeiter, jobs, protokoll, warteschlange
from .einstellungen import STAENDE, Einstellungen, lege_ordner_an
from .typen import Eingabefehler

_BEISPIEL = {
    "name": "gesamt",
    "mitte_x": "-0.75",
    "mitte_y": "0",
    "breite": "3.5",
    "groesse": "fullhd",
}
_BESCHREIBUNG = (
    "Testseite des Job-Servers. Sie ersetzt bis Stufe 4 die Bedienoberfläche.\n\n"
    "Einen Aufruf aufklappen, auf **Try it out** und dann auf **Execute** tippen. "
    "Ein fertiges Bild zeigt der Aufruf `/api/ergebnisse/{name}/bild.png`."
)


class _Antwortfehler(Exception):
    """Eine Antwort mit Fehlermeldung, zum Beispiel 404 oder 409."""

    def __init__(self, status: int, text: str):
        super().__init__(text)
        self.status = status
        self.text = text


def _fehler(status: int, text: str) -> JSONResponse:
    return JSONResponse({"fehler": text}, status_code=status)


def _zeittext(sekunden: float) -> str:
    return protokoll.zeittext(datetime.fromtimestamp(sekunden).astimezone())


def _adresse_ergebnis(name: str) -> str:
    return f"/api/ergebnisse/{quote(name, safe='')}"


# --------------------------------------------------------------------- Jobs


def _job(einstellungen: Einstellungen, stand: str, datei: Path) -> dict | None:
    """Ein Job, wie ihn der Job-Server zeigt. None, wenn die Datei gerade weitergewandert ist."""
    name = datei.stem
    try:
        angelegt = warteschlange.angelegt_am(datei)
        try:
            angaben = jobs.lies(datei)
        except Eingabefehler:
            angaben = None  # von Hand abgelegt und nicht lesbar, den Grund nennt der Arbeiter
    except OSError:
        return None
    job = {"name": name, "stand": stand, "angelegt": _zeittext(angelegt), "angaben": angaben}
    if stand == "fehler":
        try:
            text = warteschlange.fehlertext_datei(einstellungen, name).read_text(encoding="utf-8")
            job["fehler"] = text.split("\n\n")[0].strip()  # ohne die Fehlerspur
        except OSError:
            job["fehler"] = "Der Grund ist nicht festgehalten."
    if stand == "fertig" and (einstellungen.ergebnisse / name / ablage.DATEI_BESCHREIBUNG).is_file():
        job["ergebnis"] = _adresse_ergebnis(name)
    return job


def _alle_jobs(einstellungen: Einstellungen, staende=STAENDE) -> list[dict]:
    """Alle Jobs, neueste zuerst."""
    gefunden: dict[str, dict] = {}
    for stand in staende:
        for datei in warteschlange.jobs_im_stand(einstellungen, stand):
            job = _job(einstellungen, stand, datei)
            if job is not None:
                gefunden[job["name"]] = job  # wandert ein Job gerade, gilt der spätere Stand
    return sorted(
        sorted(gefunden.values(), key=lambda job: job["name"]),
        key=lambda job: datetime.fromisoformat(job["angelegt"]),
        reverse=True,
    )


def _zeitname(einstellungen: Einstellungen) -> str:
    """job-JJJJMMTT-HHMMSS, bei Gleichstand mit angehängter Zahl."""
    grund = protokoll.jetzt().strftime("job-%Y%m%d-%H%M%S")
    name, nummer = grund, 1
    while warteschlange.name_vergeben(einstellungen, name):
        nummer += 1
        name = f"{grund}-{nummer}"
    return name


# --------------------------------------------------------------- Ergebnisse


def _lies_beschreibung(einstellungen: Einstellungen, name: str) -> dict:
    ablage.pruefe_name(name)
    datei = einstellungen.ergebnisse / name / ablage.DATEI_BESCHREIBUNG
    if name.endswith(warteschlange.TEIL) or not datei.is_file():
        raise _Antwortfehler(404, f"Das Ergebnis '{name}' gibt es nicht.")
    return json.loads(datei.read_text(encoding="utf-8"))


def _ergebnisordner(einstellungen: Einstellungen) -> list[Path]:
    if not einstellungen.ergebnisse.is_dir():
        return []
    return [
        ordner
        for ordner in einstellungen.ergebnisse.iterdir()
        if not ordner.name.endswith(warteschlange.TEIL)
        and (ordner / ablage.DATEI_BESCHREIBUNG).is_file()
    ]


def _ergebnis(ordner: Path) -> dict | None:
    try:
        beschreibung = json.loads((ordner / ablage.DATEI_BESCHREIBUNG).read_text(encoding="utf-8"))
        job = beschreibung.get("job") or {}
        zeitpunkt = job.get("fertig") or beschreibung.get("erzeugt")
        if not zeitpunkt:
            zeitpunkt = _zeittext((ordner / ablage.DATEI_BESCHREIBUNG).stat().st_mtime)
        datetime.fromisoformat(zeitpunkt)
        return {
            "name": ordner.name,
            "raster": beschreibung.get("raster"),
            "elternbild": job.get("elternbild"),
            "serie": job.get("serie"),
            "zeitpunkt": zeitpunkt,
            "bild": f"{_adresse_ergebnis(ordner.name)}/{ablage.DATEI_BILD}",
        }
    except (OSError, ValueError, TypeError, AttributeError):
        return None  # kein lesbares Ergebnis, zum Beispiel von Hand verändert


# ----------------------------------------------------------- die Anwendung


def erzeuge_app(einstellungen: Einstellungen) -> FastAPI:
    """Die Anwendung des Job-Servers für diese Einstellungen."""
    lege_ordner_an(einstellungen)
    anlegen = threading.Lock()  # zwei Anfragen zugleich bekommen nie denselben Namen

    @asynccontextmanager
    async def lebenslauf(app: FastAPI):
        protokoll.schreibe(
            einstellungen, protokoll.OHNE_JOB, "server gestartet", f"Port {einstellungen.port}"
        )
        try:
            yield
        finally:
            protokoll.schreibe(einstellungen, protokoll.OHNE_JOB, "server beendet")

    app = FastAPI(
        title="KI-Mandelbrot: Job-Server",
        description=_BESCHREIBUNG,
        version=__version__,
        lifespan=lebenslauf,
        redoc_url=None,
    )

    @app.exception_handler(Eingabefehler)
    async def bei_eingabefehler(request: Request, fehler: Eingabefehler):
        return _fehler(400, str(fehler))

    @app.exception_handler(_Antwortfehler)
    async def bei_antwortfehler(request: Request, fehler: _Antwortfehler):
        return _fehler(fehler.status, fehler.text)

    @app.exception_handler(RequestValidationError)
    async def bei_unlesbarer_anfrage(request: Request, fehler: RequestValidationError):
        return _fehler(
            400,
            "Die Anfrage ist nicht lesbar. Erwartet werden die Angaben des Jobs als JSON "
            'in geschweiften Klammern, zum Beispiel {"mitte_x": "-0.75", "mitte_y": "0", '
            '"breite": "3.5", "groesse": "fullhd"}',
        )

    @app.exception_handler(HTTPException)
    async def bei_unbekannter_adresse(request: Request, fehler: HTTPException):
        if fehler.status_code == 404:
            return _fehler(404, f"Die Adresse {request.url.path} gibt es nicht.")
        if fehler.status_code == 405:
            return _fehler(405, f"{request.method} ist für {request.url.path} nicht vorgesehen.")
        return _fehler(fehler.status_code, str(fehler.detail))

    @app.get("/", include_in_schema=False)
    def startseite():
        return RedirectResponse("/docs")

    @app.get("/api/zustand", summary="Zustand: Jobs je Stand, Ergebnisse, Arbeiter")
    def zustand():
        zeichen = arbeiter.lies_lebenszeichen(einstellungen)
        return {
            "programm": f"ki-mandelbrot {__version__}",
            "jobs": {
                stand: len(warteschlange.jobs_im_stand(einstellungen, stand)) for stand in STAENDE
            },
            "ergebnisse": len(_ergebnisordner(einstellungen)),
            "arbeiter_aktiv": zeichen["aktiv"],
            "laufender_job": zeichen["job"] if zeichen["aktiv"] else None,
        }

    @app.post("/api/jobs", status_code=201, summary="Job anlegen")
    def lege_job_an(
        angaben: dict[str, Any] = Body(
            ...,
            examples=[_BEISPIEL],
            description="Die Angaben des Jobs nach R18, dazu freiwillig `name`. "
            "Mittelpunkt und Bildbreite stehen in Anführungszeichen.",
        ),
    ):
        angaben = dict(angaben)
        if "angelegt" in angaben:
            raise Eingabefehler("'angelegt' trägt der Job-Server selbst ein.")
        name = angaben.pop("name", None)
        if name is not None and (not isinstance(name, str) or not name.strip()):
            raise Eingabefehler(f"'name' muss ein Text in Anführungszeichen sein, angegeben: {name!r}")
        with anlegen:
            if name is None:
                name = _zeitname(einstellungen)
            else:
                name = ablage.pruefe_name(name.strip())
                if name.endswith(warteschlange.TEIL):
                    raise Eingabefehler(
                        f"Ein Jobname darf nicht auf '{warteschlange.TEIL}' enden, angegeben: '{name}'"
                    )
                if warteschlange.name_vergeben(einstellungen, name):
                    raise _Antwortfehler(
                        409, f"Den Jobnamen '{name}' gibt es schon. Bitte einen anderen wählen."
                    )
            jobs.pruefe(angaben, name, einstellungen)
            zeitpunkt = protokoll.jetzt()
            angaben["angelegt"] = protokoll.zeittext(zeitpunkt)
            datei = warteschlange.datei(einstellungen, "neu", name)
            jobs.schreibe(datei, angaben)
            protokoll.schreibe(
                einstellungen, name, "angelegt", "über den Job-Server", zeitpunkt=zeitpunkt
            )
        return {"name": name, "stand": "neu", "angelegt": angaben["angelegt"], "angaben": angaben}

    @app.get("/api/jobs", summary="Alle Jobs, neueste zuerst")
    def liste_jobs(stand: str | None = None):
        if stand is None:
            return _alle_jobs(einstellungen)
        if stand not in STAENDE:
            raise Eingabefehler(
                f"Den Stand '{stand}' gibt es nicht. Möglich sind " + ", ".join(STAENDE)
            )
        return _alle_jobs(einstellungen, (stand,))

    @app.get("/api/jobs/{name}", summary="Ein Job mit Stand, Angaben und bei Fehlern dem Grund")
    def zeige_job(name: str):
        ablage.pruefe_name(name)
        for _ in range(2):  # zweiter Versuch, falls der Job gerade weiterwandert
            stand = warteschlange.stand_von(einstellungen, name)
            if stand is None:
                break
            job = _job(einstellungen, stand, warteschlange.datei(einstellungen, stand, name))
            if job is not None:
                return job
        raise _Antwortfehler(404, f"Den Job '{name}' gibt es nicht.")

    @app.get("/api/ergebnisse", summary="Alle Ergebnisse, neueste zuerst")
    def liste_ergebnisse():
        ergebnisse = [e for e in map(_ergebnis, _ergebnisordner(einstellungen)) if e is not None]
        return sorted(
            sorted(ergebnisse, key=lambda e: e["name"]),
            key=lambda e: datetime.fromisoformat(e["zeitpunkt"]),
            reverse=True,
        )

    @app.get("/api/ergebnisse/{name}", summary="Beschreibung eines Ergebnisses (lauf.json)")
    def zeige_ergebnis(name: str):
        return _lies_beschreibung(einstellungen, name)

    @app.get(
        "/api/ergebnisse/{name}/bild.png",
        summary="Das Bild eines Ergebnisses",
        response_class=FileResponse,
        responses={200: {"content": {"image/png": {}}}},
    )
    def zeige_bild(name: str):
        _lies_beschreibung(einstellungen, name)
        bild = einstellungen.ergebnisse / name / ablage.DATEI_BILD
        if not bild.is_file():
            raise _Antwortfehler(404, f"Zum Ergebnis '{name}' gibt es kein Bild.")
        return FileResponse(bild, media_type="image/png")

    return app
