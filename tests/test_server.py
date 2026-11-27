"""R24: der Job-Server. Jeder Aufruf mit Erfolg und Fehler, ohne einen Port zu öffnen."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mandelbrot import __version__, arbeiter, einstellungen, kommandozeile, server, warteschlange
from mandelbrot.kommandozeile import main
from stufe3 import KLEIN, ereignisse, lege_ergebnis, lege_job, projekt, protokollzeilen


@pytest.fixture
def werte(tmp_path):
    return projekt(tmp_path)


@pytest.fixture
def seite(werte):
    return TestClient(server.erzeuge_app(werte), follow_redirects=False)


def _inhalt(werte):
    """Alle Dateien im Projektordner außer dem Protokoll, mit ihrem Inhalt."""
    return {
        str(p.relative_to(werte.projektordner)): p.read_bytes()
        for p in sorted(werte.projektordner.rglob("*"))
        if p.is_file() and werte.ereignisse not in p.parents
    }


# ------------------------------------------------------------ Job anlegen


def test_job_anlegen(werte, seite):
    antwort = seite.post("/api/jobs", json={**KLEIN, "name": "gesamt", "serie": "probe"})
    assert antwort.status_code == 201
    job = antwort.json()
    assert job["name"] == "gesamt" and job["stand"] == "neu"
    assert job["angaben"]["serie"] == "probe" and job["angaben"]["mitte_x"] == "-0.75"
    assert job["angelegt"] == job["angaben"]["angelegt"]

    datei = werte.ordner_fuer("neu") / "gesamt.json"
    gespeichert = json.loads(datei.read_text(encoding="utf-8"))
    assert gespeichert == job["angaben"]
    assert "name" not in gespeichert  # der Name ist der Dateiname
    assert ereignisse(werte, "gesamt") == ["angelegt"]
    assert not list(werte.ordner_fuer("neu").glob("*.teil"))


def test_angelegter_job_laeuft_beim_arbeiter_durch(werte, seite):
    seite.post("/api/jobs", json={**KLEIN, "name": "gesamt"})
    assert arbeiter.arbeite(werte, einmal=True, mindestalter=0) == 1
    assert ereignisse(werte, "gesamt") == ["angelegt", "gestartet", "fertig"]
    lauf = seite.get("/api/ergebnisse/gesamt").json()
    assert lauf["job"]["angelegt"] == seite.get("/api/jobs/gesamt").json()["angelegt"]


def test_job_ohne_namen_bekommt_einen_zeitnamen(werte, seite):
    erster = seite.post("/api/jobs", json=KLEIN).json()["name"]
    zweiter = seite.post("/api/jobs", json=KLEIN).json()["name"]
    dritter = seite.post("/api/jobs", json=KLEIN).json()["name"]
    assert len({erster, zweiter, dritter}) == 3
    for name in (erster, zweiter, dritter):
        assert name.startswith("job-20") and (werte.ordner_fuer("neu") / f"{name}.json").is_file()


def test_zeitname_bei_gleichstand_mit_angehaengter_zahl(werte, seite, monkeypatch):
    fest = datetime(2026, 11, 18, 20, 15, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(server.protokoll, "jetzt", lambda: fest)
    namen = [seite.post("/api/jobs", json=KLEIN).json()["name"] for _ in range(3)]
    assert namen == ["job-20261118-201530", "job-20261118-201530-2", "job-20261118-201530-3"]


@pytest.mark.parametrize(
    "angaben, stichwort",
    [
        ({"mitte_x": "-0.75", "mitte_y": "0", "groesse": "48x32"}, "breite"),
        ({**KLEIN, "mitte_x": -0.75}, "Anführungszeichen"),
        ({**KLEIN, "farbe": "rot"}, "farbe"),
        ({**KLEIN, "palette": 7}, "palette"),
        ({**KLEIN, "groesse": "riesig"}, "riesig"),
        ({**KLEIN, "elternbild": "fehlt"}, "fehlt"),
        ({**KLEIN, "name": "a/b"}, "nicht erlaubt"),
        ({**KLEIN, "name": ".."}, "nicht erlaubt"),
        ({**KLEIN, "name": 5}, "name"),
        ({**KLEIN, "name": "halb.teil"}, ".teil"),
        ({**KLEIN, "angelegt": "2026-01-01T00:00:00+01:00"}, "angelegt"),
    ],
)
def test_falsche_angaben_werden_abgewiesen(werte, seite, angaben, stichwort):
    vorher = _inhalt(werte)
    antwort = seite.post("/api/jobs", json=angaben)
    assert antwort.status_code == 400
    assert list(antwort.json()) == ["fehler"] and stichwort in antwort.json()["fehler"]
    assert _inhalt(werte) == vorher  # nichts angelegt
    assert protokollzeilen(werte) == []


@pytest.mark.parametrize("inhalt", ["kaputt", "[1, 2]", '"text"', ""])
def test_unlesbare_anfrage(werte, seite, inhalt):
    antwort = seite.post(
        "/api/jobs", content=inhalt, headers={"content-type": "application/json"}
    )
    assert antwort.status_code == 400
    assert "nicht lesbar" in antwort.json()["fehler"]
    assert _inhalt(werte) == {}


# C5: ohne Bildgröße gilt die Größe des Elternbildes, ohne beides wird abgewiesen.


def test_ohne_groesse_und_ohne_elternbild_wird_abgewiesen(werte, seite):
    ohne = {k: v for k, v in KLEIN.items() if k != "groesse"}
    antwort = seite.post("/api/jobs", json={**ohne, "name": "ohne"})
    assert antwort.status_code == 400 and "Bildgröße" in antwort.json()["fehler"]
    assert warteschlange.stand_von(werte, "ohne") is None


def test_ohne_groesse_mit_elternbild_wird_angelegt(werte, seite):
    lege_ergebnis(werte, "gesamt", raster=(40, 30))
    ohne = {k: v for k, v in KLEIN.items() if k != "groesse"}
    antwort = seite.post("/api/jobs", json={**ohne, "name": "kind", "elternbild": "gesamt"})
    assert antwort.status_code == 201
    arbeiter.arbeite(werte, einmal=True, mindestalter=0)
    lauf = seite.get("/api/ergebnisse/kind").json()
    assert lauf["raster"] == [40, 30] and lauf["job"]["elternbild"] == "gesamt"


@pytest.mark.parametrize("stand", ["neu", "laeuft", "fertig", "fehler"])
def test_vergebener_name_als_job(werte, seite, stand):
    lege_job(werte, "gesamt", stand=stand)
    antwort = seite.post("/api/jobs", json={**KLEIN, "name": "gesamt"})
    assert antwort.status_code == 409 and "gesamt" in antwort.json()["fehler"]
    assert ereignisse(werte, "gesamt") == []


def test_vergebener_name_als_ergebnis(werte, seite):
    lege_ergebnis(werte, "gesamt")
    antwort = seite.post("/api/jobs", json={**KLEIN, "name": "gesamt"})
    assert antwort.status_code == 409
    assert warteschlange.stand_von(werte, "gesamt") is None


# ------------------------------------------------------------ Jobs zeigen


def test_liste_der_jobs_neueste_zuerst(werte, seite):
    lege_job(werte, "alt", {**KLEIN, "angelegt": "2026-11-16T10:00:00+01:00"}, stand="fertig")
    lege_job(werte, "mittel", {**KLEIN, "angelegt": "2026-11-16T11:00:00+01:00"}, stand="fehler")
    lege_job(werte, "von-hand", alter=60)  # ohne 'angelegt' gilt das Änderungsdatum
    seite.post("/api/jobs", json={**KLEIN, "name": "neu"})

    jobs = seite.get("/api/jobs").json()
    assert [(j["name"], j["stand"]) for j in jobs] == [
        ("neu", "neu"), ("von-hand", "neu"), ("mittel", "fehler"), ("alt", "fertig"),
    ]
    assert [j["name"] for j in seite.get("/api/jobs?stand=neu").json()] == ["neu", "von-hand"]
    assert [j["name"] for j in seite.get("/api/jobs?stand=fertig").json()] == ["alt"]
    assert seite.get("/api/jobs?stand=laeuft").json() == []


def test_liste_der_jobs_leer(seite):
    assert seite.get("/api/jobs").json() == []


def test_liste_mit_unbekanntem_stand(seite):
    antwort = seite.get("/api/jobs?stand=bald")
    assert antwort.status_code == 400 and "bald" in antwort.json()["fehler"]


def test_liste_uebersieht_fremde_dateien(werte, seite):
    (werte.ordner_fuer("neu") / "halb.json.teil").write_text("{", encoding="utf-8")
    (werte.ordner_fuer("neu") / "notiz.txt").write_text("hallo", encoding="utf-8")
    assert seite.get("/api/jobs").json() == []


def test_ein_job_in_jedem_stand(werte, seite):
    for stand in ("neu", "laeuft", "fertig", "fehler"):
        lege_job(werte, f"job-{stand}", stand=stand)
        job = seite.get(f"/api/jobs/job-{stand}").json()
        assert job["name"] == f"job-{stand}" and job["stand"] == stand
        assert job["angaben"] == KLEIN


def test_gescheiterter_job_nennt_den_grund(werte, seite):
    lege_job(werte, "kaputt", {**KLEIN, "palette": 9})
    lege_job(werte, "unlesbar", roh="{ das ist kein JSON")
    arbeiter.arbeite(werte, einmal=True)

    job = seite.get("/api/jobs/kaputt").json()
    assert job["stand"] == "fehler" and "palette" in job["fehler"]
    unlesbar = seite.get("/api/jobs/unlesbar").json()
    assert unlesbar["stand"] == "fehler" and unlesbar["angaben"] is None
    assert "JSON" in unlesbar["fehler"]
    assert {j["name"]: "fehler" in j for j in seite.get("/api/jobs").json()} == {
        "kaputt": True, "unlesbar": True,
    }


def test_grund_ohne_fehlerspur(werte, seite):
    lege_job(werte, "kaputt", stand="fehler")
    warteschlange.fehlertext_datei(werte, "kaputt").write_text(
        "Unerwarteter Fehler: ValueError: x\n\nTraceback (most recent call last):\n  ...\n",
        encoding="utf-8",
    )
    assert seite.get("/api/jobs/kaputt").json()["fehler"] == "Unerwarteter Fehler: ValueError: x"


def test_fertiger_job_nennt_sein_ergebnis(werte, seite):
    lege_job(werte, "gesamt")
    arbeiter.arbeite(werte, einmal=True)
    job = seite.get("/api/jobs/gesamt").json()
    assert job["stand"] == "fertig" and job["ergebnis"] == "/api/ergebnisse/gesamt"
    assert seite.get(job["ergebnis"]).status_code == 200


def test_unbekannter_job(seite):
    antwort = seite.get("/api/jobs/fehlt")
    assert antwort.status_code == 404 and "fehlt" in antwort.json()["fehler"]


# ------------------------------------------------------------- Ergebnisse


def test_ergebnisse_neueste_zuerst(werte, seite):
    assert seite.get("/api/ergebnisse").json() == []
    lege_job(werte, "gesamt", {**KLEIN, "serie": "probe"})
    arbeiter.arbeite(werte, einmal=True)
    lege_job(werte, "kind", {"mitte_x": "-0.75", "mitte_y": "0.1", "breite": "0.5",
                             "elternbild": "gesamt"})
    arbeiter.arbeite(werte, einmal=True)
    # Reste, die keine Ergebnisse sind
    (werte.ergebnisse / "halb.teil").mkdir()
    (werte.ergebnisse / "halb.teil" / "lauf.json").write_text("{}", encoding="utf-8")
    (werte.ergebnisse / "leer").mkdir()
    # Der Zeitpunkt zählt auf die Sekunde. Die Reihenfolge soll hier eindeutig sein.
    datei = werte.ergebnisse / "gesamt" / "lauf.json"
    lauf = json.loads(datei.read_text(encoding="utf-8"))
    lauf["job"]["fertig"] = "2026-11-16T10:00:00+01:00"
    datei.write_text(json.dumps(lauf), encoding="utf-8")

    ergebnisse = seite.get("/api/ergebnisse").json()
    assert [e["name"] for e in ergebnisse] == ["kind", "gesamt"]
    kind, gesamt = ergebnisse
    assert gesamt == {
        "name": "gesamt",
        "raster": [48, 32],
        "elternbild": None,
        "serie": "probe",
        "zeitpunkt": "2026-11-16T10:00:00+01:00",
        "bild": "/api/ergebnisse/gesamt/bild.png",
    }
    assert kind["elternbild"] == "gesamt" and kind["raster"] == [48, 32]
    assert seite.get(kind["bild"]).status_code == 200


def test_beschreibung_eines_ergebnisses(werte, seite):
    lege_job(werte, "gesamt")
    arbeiter.arbeite(werte, einmal=True)
    antwort = seite.get("/api/ergebnisse/gesamt")
    assert antwort.status_code == 200
    gespeichert = json.loads((werte.ergebnisse / "gesamt" / "lauf.json").read_text(encoding="utf-8"))
    assert antwort.json() == gespeichert and antwort.json()["job"]["name"] == "gesamt"


def test_bild_eines_ergebnisses(werte, seite):
    lege_job(werte, "gesamt")
    arbeiter.arbeite(werte, einmal=True)
    antwort = seite.get("/api/ergebnisse/gesamt/bild.png")
    assert antwort.status_code == 200
    assert antwort.headers["content-type"] == "image/png"
    assert antwort.content == (werte.ergebnisse / "gesamt" / "bild.png").read_bytes()


def test_unbekanntes_ergebnis(werte, seite):
    for adresse in ("/api/ergebnisse/fehlt", "/api/ergebnisse/fehlt/bild.png"):
        antwort = seite.get(adresse)
        assert antwort.status_code == 404 and "fehlt" in antwort.json()["fehler"]


def test_halbes_ergebnis_ist_nicht_sichtbar(werte, seite):
    ordner = lege_ergebnis(werte, "halb.teil")
    (ordner / "bild.png").write_bytes(b"x")
    assert seite.get("/api/ergebnisse/halb.teil").status_code == 404
    assert seite.get("/api/ergebnisse/halb.teil/bild.png").status_code == 404
    assert seite.get("/api/zustand").json()["ergebnisse"] == 0


def test_ergebnis_ohne_bild(werte, seite):
    lege_ergebnis(werte, "ohne-bild")
    assert seite.get("/api/ergebnisse/ohne-bild").status_code == 200
    assert seite.get("/api/ergebnisse/ohne-bild/bild.png").status_code == 404


# ------------------------------------------------- Namen mit Pfadzeichen


@pytest.mark.parametrize(
    "adresse",
    [
        "/api/jobs/a%5Cb",
        "/api/jobs/a%3Ab",
        "/api/ergebnisse/..%5C..%5Cmandelbrot",
        "/api/ergebnisse/a%2Ab/bild.png",
        "/api/ergebnisse/C%3Ageheim",
    ],
)
def test_namen_mit_pfadzeichen_werden_abgewiesen(seite, adresse):
    antwort = seite.get(adresse)
    assert antwort.status_code == 400 and "nicht erlaubt" in antwort.json()["fehler"]


@pytest.mark.parametrize(
    "adresse",
    [
        "/api/jobs/..%2Fgeheim",
        "/api/ergebnisse/..%2F..%2Fgeheim",
        "/api/ergebnisse/%2E%2E/geheim.json",
        "/api/ergebnisse/..%2F..%2Fgeheim.png/bild.png",
    ],
)
def test_kein_weg_aus_den_ordnern(werte, seite, adresse):
    (werte.projektordner / "geheim.json").write_text('{"geheim": 1}', encoding="utf-8")
    (werte.projektordner / "geheim.png").write_bytes(b"geheim")
    antwort = seite.get(adresse)
    assert antwort.status_code in (400, 404)
    assert "geheim\": 1" not in antwort.text and antwort.content != b"geheim"


# ---------------------------------------------------------------- Zustand


def test_zustand_ohne_lebenszeichen(werte, seite):
    assert seite.get("/api/zustand").json() == {
        "programm": f"ki-mandelbrot {__version__}",
        "jobs": {"neu": 0, "laeuft": 0, "fertig": 0, "fehler": 0},
        "ergebnisse": 0,
        "arbeiter_aktiv": False,
        "laufender_job": None,
    }


def test_zustand_zaehlt_jobs_und_ergebnisse(werte, seite):
    lege_job(werte, "eins")
    lege_job(werte, "zwei")
    lege_job(werte, "kaputt", {**KLEIN, "palette": 9}, alter=60)
    arbeiter.arbeite(werte, einmal=True, soll_enden=iter([False, False, True]).__next__)
    zustand = seite.get("/api/zustand").json()
    assert zustand["jobs"] == {"neu": 1, "laeuft": 0, "fertig": 1, "fehler": 1}
    assert zustand["ergebnisse"] == 1


def test_zustand_mit_lebenszeichen(werte, seite):
    arbeiter.schreibe_lebenszeichen(werte, None)
    zustand = seite.get("/api/zustand").json()
    assert zustand["arbeiter_aktiv"] is True and zustand["laufender_job"] is None

    arbeiter.schreibe_lebenszeichen(werte, "gesamt")
    zustand = seite.get("/api/zustand").json()
    assert zustand["arbeiter_aktiv"] is True and zustand["laufender_job"] == "gesamt"

    arbeiter.schreibe_lebenszeichen(werte, None, beendet=True)
    assert seite.get("/api/zustand").json()["arbeiter_aktiv"] is False


def test_zustand_mit_altem_lebenszeichen(werte, seite):
    (werte.jobs / arbeiter.LEBENSZEICHEN).write_text(
        json.dumps({"zeit": "2026-11-16T10:00:00+01:00", "job": None}), encoding="utf-8"
    )
    zustand = seite.get("/api/zustand").json()
    assert zustand["arbeiter_aktiv"] is False and zustand["laufender_job"] is None


# -------------------------------------------------- Testseite und Rahmen


def test_startseite_leitet_auf_die_testseite(seite):
    antwort = seite.get("/")
    assert antwort.status_code in (302, 307) and antwort.headers["location"] == "/docs"
    assert seite.get("/docs").status_code == 200


def test_testseite_nennt_alle_aufrufe(seite):
    wege = seite.get("/openapi.json").json()["paths"]
    assert sorted(wege) == [
        "/api/ergebnisse",
        "/api/ergebnisse/{name}",
        "/api/ergebnisse/{name}/bild.png",
        "/api/jobs",
        "/api/jobs/{name}",
        "/api/zustand",
    ]
    assert sorted(wege["/api/jobs"]) == ["get", "post"]


def test_unbekannte_adresse_und_falscher_aufruf(seite):
    antwort = seite.get("/api/gibtsnicht")
    assert antwort.status_code == 404 and "gibtsnicht" in antwort.json()["fehler"]
    antwort = seite.delete("/api/jobs/gesamt")  # Löschen gibt es in Stufe 3 nicht
    assert antwort.status_code == 405 and list(antwort.json()) == ["fehler"]


def test_server_schreibt_nur_in_neu_und_ins_protokoll(werte, seite):
    lege_job(werte, "fertig-1")
    lege_job(werte, "kaputt", {**KLEIN, "palette": 9})
    arbeiter.arbeite(werte, einmal=True)
    vorher = _inhalt(werte)
    for adresse in (
        "/api/zustand", "/api/jobs", "/api/jobs?stand=fehler", "/api/jobs/fertig-1",
        "/api/jobs/kaputt", "/api/ergebnisse", "/api/ergebnisse/fertig-1",
        "/api/ergebnisse/fertig-1/bild.png", "/api/jobs/fehlt",
    ):
        seite.get(adresse)
    assert _inhalt(werte) == vorher
    seite.post("/api/jobs", json={**KLEIN, "name": "dazu"})
    neu = set(_inhalt(werte)) - set(vorher)
    assert {p.replace("\\", "/") for p in neu} == {"_JOBS/neu/dazu.json"}


def test_start_und_ende_stehen_im_protokoll(werte):
    with TestClient(server.erzeuge_app(werte)) as seite:
        seite.get("/api/zustand")
    assert [zeile[1:3] for zeile in protokollzeilen(werte)] == [
        ["-", "server gestartet"], ["-", "server beendet"],
    ]


def test_app_legt_fehlende_ordner_an(tmp_path):
    werte = einstellungen.lade(tmp_path)
    seite = TestClient(server.erzeuge_app(werte))
    assert seite.post("/api/jobs", json={**KLEIN, "name": "gesamt"}).status_code == 201
    assert (tmp_path / "_JOBS" / "neu" / "gesamt.json").is_file()


def test_arbeiter_kommt_ohne_fastapi_aus():
    """Nur server.py braucht die neuen Pakete (technische Spec, Rahmen)."""
    probe = (
        "import sys\n"
        "from mandelbrot import kommandozeile\n"
        "geladen = [m for m in ('fastapi', 'uvicorn', 'starlette', 'mandelbrot.server') "
        "if m in sys.modules]\n"
        "raise SystemExit(', '.join(geladen) or 0)\n"
    )
    quellen = str(Path(server.__file__).parents[1])
    lauf = subprocess.run(
        [sys.executable, "-c", probe],
        env={**os.environ, "PYTHONPATH": quellen},
        capture_output=True,
        text=True,
    )
    assert lauf.returncode == 0, lauf.stderr


# ----------------------------------------------- Befehle server und start


class _Uvicorn:
    """Steht in den Tests an der Stelle von uvicorn.run. Ein Port wird nicht geöffnet."""

    def __init__(self, monkeypatch, wirkung=None):
        self.aufrufe = []
        self.wirkung = wirkung
        import uvicorn

        monkeypatch.setattr(uvicorn, "run", self)

    def __call__(self, app, **angaben):
        self.aufrufe.append((app, angaben))
        if self.wirkung is not None:
            raise self.wirkung


def test_befehl_server(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mandelbrot.toml").write_text("[server]\nport = 8123\n", encoding="utf-8")
    monkeypatch.setattr(kommandozeile, "_netzadressen", lambda: ["192.168.178.20"])
    uvicorn = _Uvicorn(monkeypatch)

    assert main(["server"]) == 0
    (app, angaben), = uvicorn.aufrufe
    assert angaben["host"] == "0.0.0.0" and angaben["port"] == 8123
    assert TestClient(app).get("/api/zustand").status_code == 200
    ausgabe = capsys.readouterr().out
    assert "http://192.168.178.20:8123/docs" in ausgabe and "http://localhost:8123/docs" in ausgabe
    assert (tmp_path / "_JOBS" / "neu").is_dir()


def test_befehl_server_nur_an_diesem_pc(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mandelbrot.toml").write_text('[server]\nadresse = "127.0.0.1"\n', encoding="utf-8")
    monkeypatch.setattr(kommandozeile, "_netzadressen", lambda: ["192.168.178.20"])
    uvicorn = _Uvicorn(monkeypatch)
    assert main(["server"]) == 0
    assert uvicorn.aufrufe[0][1]["host"] == "127.0.0.1"
    assert "192.168.178.20" not in capsys.readouterr().out


def test_befehl_server_endet_mit_strg_c(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _Uvicorn(monkeypatch, KeyboardInterrupt())
    assert main(["server"]) == 0


def test_befehl_server_bei_belegtem_port(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _Uvicorn(monkeypatch, SystemExit(1))
    assert main(["server"]) == 1
    assert "Port 8000" in capsys.readouterr().err


def test_befehl_server_mit_fehlerhaften_einstellungen(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mandelbrot.toml").write_text("[server]\nport = 0\n", encoding="utf-8")
    uvicorn = _Uvicorn(monkeypatch)
    assert main(["server"]) == 2
    assert "port" in capsys.readouterr().err and uvicorn.aufrufe == []


def test_befehl_server_ohne_fastapi(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(sys.modules, "uvicorn", None)  # als wäre das Paket nicht installiert
    assert main(["server"]) == 2
    fehler = capsys.readouterr().err
    assert "uvicorn" in fehler and "requirements.txt" in fehler


def test_netzadressen_ohne_die_eigene_schleife():
    for adresse in kommandozeile._netzadressen():
        assert not adresse.startswith("127.")


class _Arbeiterprozess:
    """Steht in den Tests an der Stelle des Arbeiter-Prozesses."""

    def __init__(self, befehl, haengt=False):
        self.befehl = befehl
        self.haengt = haengt
        self.signale = []
        self.beendet = False

    def poll(self):
        return 0 if self.beendet else None

    def send_signal(self, zeichen):
        self.signale.append(zeichen)
        self.beendet = not self.haengt

    def wait(self, timeout=None):
        if not self.beendet and timeout is not None:
            raise subprocess.TimeoutExpired(self.befehl, timeout)
        return 0

    def terminate(self):
        self.signale.append("terminate")
        self.beendet = True


@pytest.fixture
def prozesse(monkeypatch):
    gestartet = []

    def popen(befehl, **angaben):
        gestartet.append(_Arbeiterprozess(befehl))
        return gestartet[-1]

    monkeypatch.setattr(kommandozeile.subprocess, "Popen", popen)
    monkeypatch.setattr(kommandozeile.sys, "platform", "linux")
    return gestartet


def test_befehl_start_startet_arbeiter_und_server(tmp_path, monkeypatch, prozesse):
    monkeypatch.chdir(tmp_path)
    uvicorn = _Uvicorn(monkeypatch)
    assert main(["start"]) == 0
    (prozess,) = prozesse
    assert prozess.befehl == [sys.executable, "-m", "mandelbrot", "arbeiter"]
    assert len(uvicorn.aufrufe) == 1
    assert prozess.beendet and "terminate" not in prozess.signale  # ordentlich beendet


def test_befehl_start_beendet_den_arbeiter_auch_bei_belegtem_port(tmp_path, monkeypatch, prozesse):
    monkeypatch.chdir(tmp_path)
    _Uvicorn(monkeypatch, SystemExit(1))
    assert main(["start"]) == 1
    assert prozesse[0].beendet


def test_befehl_start_unter_windows(tmp_path, monkeypatch, prozesse):
    """Unter Windows erreicht Strg+C den Arbeiter von selbst. Ein Signal wird nicht geschickt."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(kommandozeile.sys, "platform", "win32")
    _Uvicorn(monkeypatch, KeyboardInterrupt())
    monkeypatch.setattr(
        _Arbeiterprozess, "wait", lambda self, timeout=None: setattr(self, "beendet", True)
    )
    assert main(["start"]) == 0
    assert prozesse[0].signale == [] and prozesse[0].beendet


def test_befehl_start_haengender_arbeiter_wird_beendet(tmp_path, monkeypatch, prozesse):
    monkeypatch.chdir(tmp_path)
    _Uvicorn(monkeypatch)
    monkeypatch.setattr(
        kommandozeile.subprocess,
        "Popen",
        lambda befehl, **angaben: prozesse.append(_Arbeiterprozess(befehl, haengt=True))
        or prozesse[-1],
    )
    assert main(["start"]) == 0
    assert prozesse[0].signale[-1] == "terminate" and prozesse[0].beendet


def test_befehl_start_mit_fehlerhaften_einstellungen(tmp_path, monkeypatch, prozesse, capsys):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mandelbrot.toml").write_text("[server]\nport = 0\n", encoding="utf-8")
    assert main(["start"]) == 2
    assert prozesse == []  # der Arbeiter wird gar nicht erst gestartet
