"""Die Befehle original, berechne, faerbe, vergleiche, arbeiter, server, start und autostart."""

from __future__ import annotations

import argparse
import re
import signal
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from . import __version__, ablage, arbeiter, autostart, berechnen, einstellungen
from .einfaerben import bild
from .original import LESETABELLE, lies_dat
from .paletten import ANZAHL_PALETTEN, palette
from .statistik import (
    MAX_BEREICHE_1991,
    MAX_BEREICHE_STANDARD,
    bereichsbreiten,
    bilde_farbstufen,
    haeufigkeit,
    pruefe_einstellungen,
)
from .typen import (
    ABBRUCHGRENZE,
    Ausschnitt,
    Bildausschnitt,
    Eingabefehler,
    pruefe_abbruchgrenze,
)
from .vergleich import vergleiche, vergleichsbild

PALETTE_STANDARD = 1
ORDNER_ORIGINALE = Path("Org_Daten")


# ---------------------------------------------------------------- Eingaben


def _ganze_zahl(text: str, name: str) -> int:
    try:
        return int(str(text).strip())
    except ValueError:
        raise Eingabefehler(f"{name} muss eine ganze Zahl sein, angegeben: '{text}'") from None


def _palette(text: str | None, standard: int) -> int:
    if text is None:
        return standard
    nummer = _ganze_zahl(text, "Die Palette")
    if not 0 <= nummer < ANZAHL_PALETTEN:
        raise Eingabefehler(f"Palette muss 0, 1, 2 oder 3 sein, angegeben: {text}")
    return nummer


def _schwelle(text: str) -> int | str:
    """Liefert eine ganze Zahl ab 0 oder das Wort 'auto'."""
    if str(text).strip().lower() == "auto":
        return "auto"
    schwelle = _ganze_zahl(text, "Die Schwelle")
    if schwelle < 0:
        raise Eingabefehler(f"Die Schwelle darf nicht negativ sein, angegeben: {text}")
    return schwelle


def _lauf_ordner(name: str) -> Path:
    """Prüft den Namen, bevor daraus ein Pfad wird (sonst ginge 'a/b' durch)."""
    return ablage.AUSGABE / ablage.pruefe_name(name)


def _pruefe_frei(ordner: Path, ueberschreiben: bool) -> None:
    """Bricht vor der Rechnung ab, wenn der Lauf schon existiert."""
    if ordner.exists() and not ueberschreiben:
        raise Eingabefehler(
            f"Der Lauf '{ordner.name}' existiert schon. "
            "Mit --ueberschreiben wird er ersetzt, mit --name bekommt der "
            "neue Lauf einen anderen Namen."
        )


def _zeitname() -> str:
    return datetime.now().strftime("lauf-%Y%m%d-%H%M%S")


def _prozent(anteil: float) -> str:
    return f"{anteil * 100:.2f}".replace(".", ",") + " %"


# --------------------------------------------------------------- Statistik


def _statistik(
    roh: np.ndarray, schwelle: int | str, max_bereiche: int, grenze: int = ABBRUCHGRENZE
):
    """Bildet Farbstufen und liefert sie mit dem Statistik-Teil für lauf.json."""
    return bilde_farbstufen(roh, schwelle, max_bereiche, grenze)


# ----------------------------------------------------------------- Befehle


def _befehl_original(args) -> int:
    faktor = None if args.faktor is None else _ganze_zahl(args.faktor, "Der Faktor")
    nummer = _palette(args.palette, PALETTE_STANDARD)
    original = lies_dat(args.datei, faktor)
    name = args.name or f"{Path(original.name).stem}-palette{nummer}"
    ordner = _lauf_ordner(name)
    _pruefe_frei(ordner, args.ueberschreiben)

    angaben = ablage.beschreibung("original", original.nachrechnung, nummer)
    angaben["quelldatei"] = original.name
    angaben["faktor"] = original.faktor
    angaben["ausschnitt_kopfzeile"] = original.kopfzeile.als_text()
    ablage.schreibe_lauf(
        ordner,
        beschreibung=angaben,
        stufen=original.stufen,
        bild=bild(original.stufen, palette(nummer)),
        ueberschreiben=args.ueberschreiben,
    )
    print(f"{original.name} gelesen, Palette {nummer}.")
    print(f"Lauf: {ordner}")
    return 0


_FORM_1991 = ("xmin", "xmax", "ymin", "ymax")
_FORM_NEU = ("mitte_x", "mitte_y", "breite", "groesse")


def _optionen(namen) -> str:
    return ", ".join("--" + name.replace("_", "-") for name in namen)


def _befehl_berechne(args) -> int:
    wie_1991 = [n for n in _FORM_1991 if getattr(args, n) is not None]
    neu = [n for n in _FORM_NEU if getattr(args, n) is not None]
    if wie_1991 and neu:
        raise Eingabefehler(
            "Bitte nur eine Form benutzen: entweder "
            f"{_optionen(_FORM_1991)} oder {_optionen(_FORM_NEU)}. "
            f"Angegeben sind {_optionen(wie_1991 + neu)}"
        )
    if not wie_1991 and not neu:
        raise Eingabefehler(
            f"Es fehlt der Ausschnitt: entweder {_optionen(_FORM_1991)} "
            f"oder {_optionen(_FORM_NEU)}"
        )
    form, vorhanden = (_FORM_NEU, neu) if neu else (_FORM_1991, wie_1991)
    fehlend = [n for n in form if n not in vorhanden]
    if fehlend:
        raise Eingabefehler("Es fehlt: " + _optionen(fehlend))

    grenze = ABBRUCHGRENZE
    if args.abbruchgrenze is not None:
        grenze = pruefe_abbruchgrenze(_ganze_zahl(args.abbruchgrenze, "Die Abbruchgrenze"))
    if neu:
        gegenstand = Bildausschnitt.aus_text(
            args.mitte_x, args.mitte_y, args.breite, args.groesse
        )
        berechnen.pruefe_genauigkeit(gegenstand)  # Fehler nach R15 vor der Rechnung
    else:
        gegenstand = Ausschnitt.aus_text(args.xmin, args.xmax, args.ymin, args.ymax)
    nummer = _palette(args.palette, PALETTE_STANDARD)
    schwelle = _schwelle(args.schwelle or "auto")
    max_bereiche = (
        MAX_BEREICHE_STANDARD
        if args.max_bereiche is None
        else _ganze_zahl(args.max_bereiche, "Die Höchstzahl der Bereiche")
    )
    pruefe_einstellungen(0, max_bereiche)
    ordner = _lauf_ordner(args.name or _zeitname())
    _pruefe_frei(ordner, args.ueberschreiben)

    if neu:
        roh, glatt, warnungen = berechnen.berechne_bild(gegenstand, grenze)
        for warnung in warnungen:
            print(f"Warnung: {warnung}", file=sys.stderr)
    else:
        # Die Form wie 1991 bleibt wie in Stufe 1, ohne gebrochene Abbruchwerte.
        roh, glatt = berechnen.abbruchwerte(gegenstand, grenze=grenze), None
    stufen, statistik = _statistik(roh, schwelle, max_bereiche, grenze)
    angaben = ablage.beschreibung("berechnet", gegenstand, nummer, grenze)
    angaben["statistik"] = statistik
    ablage.schreibe_lauf(
        ordner,
        beschreibung=angaben,
        stufen=stufen,
        bild=bild(stufen, palette(nummer)),
        roh=roh,
        glatt=glatt,
        ueberschreiben=args.ueberschreiben,
    )
    groesse = f"{roh.shape[0]} x {roh.shape[1]}"
    print(
        f"Berechnet: {groesse} Bildpunkte, Abbruchgrenze {grenze}, "
        f"Schwelle {statistik['schwelle']}, {statistik['bereiche']} Bereiche, "
        f"Palette {nummer}."
    )
    print(f"Lauf: {ordner}")
    return 0


def _befehl_faerbe(args) -> int:
    quelle = ablage.lies_lauf(args.lauf)
    alt = quelle.beschreibung
    nummer = _palette(args.palette, alt["palette"])
    ordner = _lauf_ordner(args.name or _zeitname())
    _pruefe_frei(ordner, args.ueberschreiben)

    grenze = alt.get("abbruchgrenze", ABBRUCHGRENZE)
    angaben = ablage.beschreibung(
        "neu eingefärbt", ablage.gegenstand_aus(alt), nummer, grenze
    )
    angaben["aus_lauf"] = quelle.ordner.name
    for schluessel in ("quelldatei", "faktor", "ausschnitt_kopfzeile"):
        if schluessel in alt:
            angaben[schluessel] = alt[schluessel]

    if quelle.roh is None:
        if args.schwelle is not None or args.max_bereiche is not None:
            raise Eingabefehler(
                f"Der Lauf '{quelle.ordner.name}' enthält keine Abbruchwerte, "
                "weil er aus einer Originaldatei stammt. Hier lässt sich nur "
                "die Palette ändern, nicht die Schwelle."
            )
        stufen = quelle.stufen
    else:
        alte_statistik = alt.get("statistik", {})
        if args.schwelle is not None:
            schwelle = _schwelle(args.schwelle)
        elif alte_statistik.get("schwelle_automatisch", True):
            schwelle = "auto"
        else:
            schwelle = alte_statistik["schwelle"]
        if args.max_bereiche is not None:
            max_bereiche = _ganze_zahl(args.max_bereiche, "Die Höchstzahl der Bereiche")
        else:
            max_bereiche = alte_statistik.get("max_bereiche", MAX_BEREICHE_STANDARD)
        stufen, statistik = _statistik(quelle.roh, schwelle, max_bereiche, grenze)
        angaben["statistik"] = statistik

    ablage.schreibe_lauf(
        ordner,
        beschreibung=angaben,
        stufen=stufen,
        bild=bild(stufen, palette(nummer)),
        roh=quelle.roh,
        glatt=quelle.glatt,
        ueberschreiben=args.ueberschreiben,
    )
    print(f"Neu eingefärbt aus '{quelle.ordner.name}', Palette {nummer}.")
    print(f"Lauf: {ordner}")
    return 0


def _befehl_vergleiche(args) -> int:
    nummer = _palette(args.palette, PALETTE_STANDARD)
    if args.datei is not None:
        dateien = [Path(args.datei)]
    else:
        if not ORDNER_ORIGINALE.is_dir():
            raise Eingabefehler(
                f"Der Ordner {ORDNER_ORIGINALE} fehlt. Bitte den Befehl aus dem "
                "Ordner des Repos aufrufen."
            )
        dateien = [ORDNER_ORIGINALE / name for name in LESETABELLE]
    schwelle_angabe = None
    if args.schwelle is not None:
        schwelle_angabe = _schwelle(args.schwelle)
        if schwelle_angabe == "auto":
            raise Eingabefehler(
                "Beim Vergleich muss die Schwelle eine Zahl sein. Ohne Angabe "
                "gilt die Schwelle von 1991 aus der Lesetabelle."
            )

    originale = []
    for datei in dateien:
        original = lies_dat(datei)
        if original.regel is None:
            raise Eingabefehler(
                f"{datei.name} steht nicht in der Lesetabelle. Vergleichen "
                "lassen sich nur die fünf Originale."
            )
        ordner = _lauf_ordner(f"vergleich-{Path(original.name).stem}")
        _pruefe_frei(ordner, args.ueberschreiben)
        originale.append((original, ordner))

    zeilen, alles_bestanden = [], True
    for original, ordner in originale:
        regel = original.regel
        schwelle = regel.schwelle_1991 if schwelle_angabe is None else schwelle_angabe
        roh = berechnen.abbruchwerte(original.nachrechnung)
        menge, stufen_anteil, neu = vergleiche(
            original.stufen, roh, schwelle, MAX_BEREICHE_1991
        )
        bestanden = menge >= regel.grenze_menge and (
            regel.grenze_stufen is None or stufen_anteil >= regel.grenze_stufen
        )
        alles_bestanden = alles_bestanden and bestanden

        breiten = bereichsbreiten(haeufigkeit(roh), schwelle, MAX_BEREICHE_1991)
        farben = palette(nummer)
        angaben = ablage.beschreibung("berechnet", original.nachrechnung, nummer)
        angaben["quelldatei"] = original.name
        angaben["statistik"] = {
            "schwelle": schwelle,
            "schwelle_automatisch": False,
            "max_bereiche": MAX_BEREICHE_1991,
            "bereiche": len(breiten),
            "breiten": breiten,
        }
        angaben["vergleich"] = {
            "menge": round(menge, 6),
            "stufen": round(stufen_anteil, 6),
            "grenze_menge": regel.grenze_menge,
            "grenze_stufen": regel.grenze_stufen,
            "bestanden": bool(bestanden),
        }
        ablage.schreibe_lauf(
            ordner,
            beschreibung=angaben,
            stufen=neu,
            bild=bild(neu, farben),
            roh=roh,
            vergleichsbild=vergleichsbild(original.stufen, neu, farben),
            ueberschreiben=args.ueberschreiben,
        )
        zeilen.append(
            (
                original.name,
                str(schwelle),
                _prozent(menge),
                _prozent(regel.grenze_menge),
                _prozent(stufen_anteil),
                "keine" if regel.grenze_stufen is None else _prozent(regel.grenze_stufen),
                "bestanden" if bestanden else "NICHT bestanden",
            )
        )

    kopf = ("Datei", "Schwelle", "Menge", "Grenze", "Stufen", "Grenze", "Urteil")
    breiten_spalten = [max(len(z[i]) for z in [kopf, *zeilen]) for i in range(len(kopf))]
    for zeile in [kopf, *zeilen]:
        print("  ".join(text.ljust(breite) for text, breite in zip(zeile, breiten_spalten)).rstrip())
    print(f"Vergleichsbilder: {ablage.AUSGABE / 'vergleich-*' / ablage.DATEI_VERGLEICH}")
    return 0 if alles_bestanden else 1


def _befehl_arbeiter(args) -> int:
    werte = einstellungen.lade()
    einstellungen.lege_ordner_an(werte)
    print(f"Arbeiter läuft. Warteschlange: {werte.ordner_fuer('neu')}")
    if not args.einmal:
        print("Beenden mit Strg+C. Ein laufender Job wird beim nächsten Start neu gerechnet.")
    try:
        anzahl = arbeiter.arbeite(werte, einmal=args.einmal)
    except KeyboardInterrupt:
        print("Arbeiter beendet.")
        return 0
    print(f"Arbeiter beendet. Bearbeitete Jobs: {anzahl}")
    return 0


def _netzadressen() -> list[str]:
    """Die Adressen dieses PCs im Heimnetz, soweit sie sich ermitteln lassen."""
    adressen = []
    try:  # Die Adresse, über die der PC andere Geräte erreicht. Gesendet wird dabei nichts.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as verbindung:
            verbindung.connect(("192.0.2.1", 9))
            adressen.append(verbindung.getsockname()[0])
    except OSError:
        pass
    try:
        adressen += socket.gethostbyname_ex(socket.gethostname())[2]
    except OSError:
        pass
    return list(dict.fromkeys(a for a in adressen if not a.startswith(("127.", "0."))))


def _starte_server(werte) -> int:
    """Lässt den Job-Server laufen, bis Strg+C gedrückt wird."""
    try:
        import uvicorn

        from . import server
    except ImportError as fehler:
        raise Eingabefehler(
            f"Für den Job-Server fehlt ein Paket ({fehler.name}). Bitte einmal "
            "'python -m pip install -r requirements.txt' aufrufen."
        ) from None
    einstellungen.lege_ordner_an(werte)
    print(f"Job-Server startet auf Port {werte.port}. Beenden mit Strg+C.")
    print(f"Testseite an diesem PC:  http://localhost:{werte.port}/docs")
    if werte.adresse in ("0.0.0.0", "::"):
        for adresse in _netzadressen():
            print(f"Testseite im Heimnetz:   http://{adresse}:{werte.port}/docs")
    else:
        print(f"Der Job-Server hört nur auf die Adresse {werte.adresse}.")
    sys.stdout.flush()
    try:
        uvicorn.run(
            server.erzeuge_app(werte), host=werte.adresse, port=werte.port, log_level="warning"
        )
    except KeyboardInterrupt:
        pass
    except SystemExit:  # so meldet uvicorn, dass es nicht starten konnte
        print(
            f"Fehler: Der Job-Server konnte nicht starten. Vermutlich ist der Port "
            f"{werte.port} schon belegt, zum Beispiel durch einen zweiten Job-Server.",
            file=sys.stderr,
        )
        return 1
    print("Job-Server beendet.")
    return 0


def _befehl_server(args) -> int:
    return _starte_server(einstellungen.lade())


def _beende_arbeiter(prozess) -> None:
    """Beendet den Arbeiter. Ein laufender Job wird beim nächsten Start neu gerechnet (R23)."""
    if prozess.poll() is None and not sys.platform.startswith("win"):
        prozess.send_signal(signal.SIGINT)  # unter Windows hat ihn Strg+C schon erreicht
    try:
        prozess.wait(timeout=5)
    except subprocess.TimeoutExpired:
        prozess.terminate()
        prozess.wait()


def _befehl_start(args) -> int:
    werte = einstellungen.lade()
    einstellungen.lege_ordner_an(werte)
    prozess = subprocess.Popen([sys.executable, "-m", "mandelbrot", "arbeiter"])
    try:
        return _starte_server(werte)
    finally:
        _beende_arbeiter(prozess)


def _befehl_autostart(args) -> int:
    if args.schalter is None:
        print("Der Autostart ist " + ("an." if autostart.ist_an() else "aus."))
    elif args.schalter == "an":
        ziel = autostart.schalte_an(Path.cwd())
        print(f"Der Autostart ist an. Angelegt: {ziel}")
    elif args.schalter == "aus":
        war_an = autostart.schalte_aus()
        print("Der Autostart ist aus." if war_an else "Der Autostart war schon aus.")
    else:
        raise Eingabefehler(
            f"Nach autostart steht 'an' oder 'aus', angegeben: '{args.schalter}'"
        )
    return 0


# ------------------------------------------------------------------ Parser


class _Parser(argparse.ArgumentParser):
    """Meldet Eingabefehler auf Deutsch, statt das Programm zu beenden."""

    _MUSTER = (
        (r"the following arguments are required: (.*)", r"Es fehlt: \1"),
        (r"unrecognized arguments: (.*)", r"Unbekannte Angabe: \1"),
        (r"argument (.*): expected one argument", r"Zu \1 fehlt der Wert"),
        (
            r"argument (.*): invalid choice: (.*) \(choose from (.*)\)",
            r"Unbekannter Befehl \2. Möglich sind: \3",
        ),
    )

    def error(self, message):
        for muster, deutsch in self._MUSTER:
            if re.fullmatch(muster, message):
                message = re.sub(muster, deutsch, message)
                break
        raise Eingabefehler(f"{message}. Hilfe: python -m mandelbrot --help")


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="python -m mandelbrot",
        description="Richards Mandelbrot-Pipeline von 1991 in Python (Stufe 1).",
    )
    parser.add_argument("--version", action="version", version=f"ki-mandelbrot {__version__}")
    befehle = parser.add_subparsers(dest="befehl", metavar="BEFEHL", required=True)

    def gemeinsam(p, mit_statistik: bool):
        if mit_statistik:
            p.add_argument("--schwelle", help="ganze Zahl ab 0 oder 'auto'")
            p.add_argument("--max-bereiche", help="Höchstzahl der Bereiche, 1 bis 256")
        p.add_argument("--palette", help="Palette 0 bis 3")
        p.add_argument("--name", help="Name des Laufs unter ausgabe/")
        p.add_argument(
            "--ueberschreiben",
            action="store_true",
            help="einen vorhandenen Lauf gleichen Namens ersetzen",
        )

    p = befehle.add_parser("original", help="eine .DAT-Datei von 1991 als Bild ausgeben")
    p.add_argument("datei", metavar="DATEI", help="Pfad der .DAT-Datei")
    p.add_argument("--faktor", help="Faktor der Kopfzeile, nur für unbekannte Dateien")
    gemeinsam(p, mit_statistik=False)
    p.set_defaults(funktion=_befehl_original)

    p = befehle.add_parser("berechne", help="einen Ausschnitt neu rechnen")
    for seite in ("xmin", "xmax", "ymin", "ymax"):
        p.add_argument(f"--{seite}", help="Form wie 1991: Dezimalzahl, zum Beispiel --xmin=-2.1")
    p.add_argument("--mitte-x", help="neue Form: Mittelpunkt, zum Beispiel --mitte-x=-0.75")
    p.add_argument("--mitte-y", help="neue Form: Mittelpunkt, zum Beispiel --mitte-y=0")
    p.add_argument("--breite", help="neue Form: Bildbreite in der Zahlenebene")
    p.add_argument("--groesse", help="neue Form: hd, fullhd, wqhd, ipad oder BREITExHÖHE")
    p.add_argument("--abbruchgrenze", help="10 bis 1000000, Standard 1005")
    gemeinsam(p, mit_statistik=True)
    p.set_defaults(funktion=_befehl_berechne)

    p = befehle.add_parser("faerbe", help="einen Lauf neu einfärben, ohne neu zu rechnen")
    p.add_argument("lauf", metavar="LAUF", help="Ordner eines Laufs, zum Beispiel ausgabe/gesamt")
    gemeinsam(p, mit_statistik=True)
    p.set_defaults(funktion=_befehl_faerbe)

    p = befehle.add_parser("vergleiche", help="Originale nachrechnen und vergleichen")
    p.add_argument("datei", metavar="DATEI", nargs="?", help="ohne Angabe: alle fünf Originale")
    p.add_argument("--schwelle", help="ganze Zahl ab 0, ohne Angabe die Schwelle von 1991")
    p.add_argument("--palette", help="Palette 0 bis 3")
    p.add_argument(
        "--ueberschreiben",
        action="store_true",
        help="vorhandene Vergleichsläufe ersetzen",
    )
    p.set_defaults(funktion=_befehl_vergleiche)

    p = befehle.add_parser("arbeiter", help="die Warteschlange in _JOBS abarbeiten")
    p.add_argument(
        "--einmal",
        action="store_true",
        help="alle wartenden Jobs abarbeiten und dann enden",
    )
    p.set_defaults(funktion=_befehl_arbeiter)

    p = befehle.add_parser("server", help="den Job-Server für das Heimnetz starten")
    p.set_defaults(funktion=_befehl_server)

    p = befehle.add_parser("start", help="Arbeiter und Job-Server zusammen starten")
    p.set_defaults(funktion=_befehl_start)

    p = befehle.add_parser("autostart", help="Autostart unter Windows zeigen, an- oder ausschalten")
    p.add_argument("schalter", metavar="an|aus", nargs="?", help="ohne Angabe: Stand zeigen")
    p.set_defaults(funktion=_befehl_autostart)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        return args.funktion(args)
    except Eingabefehler as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 2
