"""Die Befehle original, berechne, faerbe und vergleiche."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np

from . import __version__, ablage, berechnen
from .einfaerben import bild
from .original import LESETABELLE, lies_dat
from .paletten import ANZAHL_PALETTEN, palette
from .statistik import (
    MAX_BEREICHE_1991,
    MAX_BEREICHE_STANDARD,
    automatische_schwelle,
    bereichsbreiten,
    farbstufen,
    haeufigkeit,
    pruefe_einstellungen,
    stufentabelle,
)
from .typen import Ausschnitt, Eingabefehler
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


def _statistik(roh: np.ndarray, schwelle: int | str, max_bereiche: int):
    """Bildet Farbstufen und liefert sie mit dem Statistik-Teil für lauf.json."""
    zaehlung = haeufigkeit(roh)
    automatisch = schwelle == "auto"
    if automatisch:
        pruefe_einstellungen(0, max_bereiche)
        schwelle = automatische_schwelle(zaehlung, max_bereiche)
    pruefe_einstellungen(schwelle, max_bereiche)
    breiten = bereichsbreiten(zaehlung, schwelle, max_bereiche)
    stufen = farbstufen(roh, stufentabelle(breiten))
    angaben = {
        "schwelle": schwelle,
        "schwelle_automatisch": automatisch,
        "max_bereiche": max_bereiche,
        "bereiche": len(breiten),
        "breiten": breiten,
    }
    return stufen, angaben


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


def _befehl_berechne(args) -> int:
    fehlend = [
        f"--{n}" for n in ("xmin", "xmax", "ymin", "ymax") if getattr(args, n) is None
    ]
    if fehlend:
        raise Eingabefehler("Es fehlt: " + ", ".join(fehlend))
    ausschnitt = Ausschnitt.aus_text(args.xmin, args.xmax, args.ymin, args.ymax)
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

    roh = berechnen.abbruchwerte(ausschnitt)
    stufen, statistik = _statistik(roh, schwelle, max_bereiche)
    angaben = ablage.beschreibung("berechnet", ausschnitt, nummer)
    angaben["statistik"] = statistik
    ablage.schreibe_lauf(
        ordner,
        beschreibung=angaben,
        stufen=stufen,
        bild=bild(stufen, palette(nummer)),
        roh=roh,
        ueberschreiben=args.ueberschreiben,
    )
    print(
        f"Berechnet: Schwelle {statistik['schwelle']}, "
        f"{statistik['bereiche']} Bereiche, Palette {nummer}."
    )
    print(f"Lauf: {ordner}")
    return 0


def _befehl_faerbe(args) -> int:
    quelle = ablage.lies_lauf(args.lauf)
    alt = quelle.beschreibung
    nummer = _palette(args.palette, alt["palette"])
    ordner = _lauf_ordner(args.name or _zeitname())
    _pruefe_frei(ordner, args.ueberschreiben)

    angaben = ablage.beschreibung("neu eingefärbt", ablage.ausschnitt_aus(alt), nummer)
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
        stufen, statistik = _statistik(quelle.roh, schwelle, max_bereiche)
        angaben["statistik"] = statistik

    ablage.schreibe_lauf(
        ordner,
        beschreibung=angaben,
        stufen=stufen,
        bild=bild(stufen, palette(nummer)),
        roh=quelle.roh,
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
        p.add_argument(f"--{seite}", help="Dezimalzahl, zum Beispiel --xmin=-2.1")
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
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        return args.funktion(args)
    except Eingabefehler as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        return 2
