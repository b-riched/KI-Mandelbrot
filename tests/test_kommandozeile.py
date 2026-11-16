"""Die vier Befehle, jeweils in einem temporären Ordner (A4, A5)."""

import json

import numpy as np
import pytest
from PIL import Image

from mandelbrot import berechnen
from mandelbrot.kommandozeile import main

# Ein Ausschnitt weit außerhalb der Menge: Die Rechnung ist sofort fertig.
SCHNELL = ["--xmin=0,5", "--xmax=2", "--ymin=0,5", "--ymax=2"]


@pytest.fixture(autouse=True)
def im_temporaeren_ordner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _beschreibung(tmp_path, name):
    return json.loads((tmp_path / "ausgabe" / name / "lauf.json").read_text(encoding="utf-8"))


def test_berechne_legt_vollstaendigen_lauf_an(tmp_path):
    assert main(["berechne", *SCHNELL, "--name", "probe"]) == 0
    ordner = tmp_path / "ausgabe" / "probe"
    assert sorted(p.name for p in ordner.iterdir()) == [
        "bild.png", "lauf.json", "roh.npy", "stufen.npy",
    ]
    inhalt = _beschreibung(tmp_path, "probe")
    assert inhalt["herkunft"] == "berechnet"
    # Koordinaten stehen so da, wie sie eingegeben wurden, mit Punkt statt Komma.
    assert inhalt["ausschnitt"] == {"xmin": "0.5", "xmax": "2", "ymin": "0.5", "ymax": "2"}
    statistik = inhalt["statistik"]
    assert statistik["schwelle_automatisch"] is True
    assert statistik["max_bereiche"] == 255
    assert statistik["bereiche"] == len(statistik["breiten"]) <= 255
    assert sum(statistik["breiten"]) == 1005
    assert inhalt["palette"] == 1


def test_berechne_mit_fester_schwelle_und_256_bereichen(tmp_path):
    befehl = ["berechne", *SCHNELL, "--name", "fest", "--schwelle", "0",
              "--max-bereiche", "256", "--palette", "0"]
    assert main(befehl) == 0
    statistik = _beschreibung(tmp_path, "fest")["statistik"]
    assert statistik["schwelle"] == 0 and statistik["schwelle_automatisch"] is False
    assert statistik["bereiche"] == 256


def test_ohne_namen_heisst_der_lauf_nach_der_uhrzeit(tmp_path):
    assert main(["berechne", *SCHNELL]) == 0
    (ordner,) = (tmp_path / "ausgabe").iterdir()
    assert ordner.name.startswith("lauf-") and len(ordner.name) == len("lauf-20261116-175500")


def test_original(tmp_path, org_daten):
    assert main(["original", str(org_daten / "M0.DAT")]) == 0
    ordner = tmp_path / "ausgabe" / "M0-palette1"
    assert not (ordner / "roh.npy").exists()
    inhalt = _beschreibung(tmp_path, "M0-palette1")
    assert inhalt["herkunft"] == "original"
    assert inhalt["quelldatei"] == "M0.DAT" and inhalt["faktor"] == 1000
    assert inhalt["ausschnitt"]["xmin"] == "-2.1"
    assert inhalt["ausschnitt_kopfzeile"]["xmin"] == "-2.099"
    assert "statistik" not in inhalt
    with Image.open(ordner / "bild.png") as png:
        assert png.size == (480, 480)


def test_faerbe_rechnet_nicht_neu(tmp_path, monkeypatch):
    assert main(["berechne", *SCHNELL, "--name", "quelle"]) == 0

    def darf_nicht_laufen(*args, **kwargs):
        raise AssertionError("faerbe hat neu gerechnet")

    monkeypatch.setattr(berechnen, "abbruchwerte", darf_nicht_laufen)
    befehl = ["faerbe", "ausgabe/quelle", "--palette", "2", "--schwelle", "3",
              "--name", "bunt"]
    assert main(befehl) == 0
    inhalt = _beschreibung(tmp_path, "bunt")
    assert inhalt["herkunft"] == "neu eingefärbt"
    assert inhalt["aus_lauf"] == "quelle"
    assert inhalt["palette"] == 2
    assert inhalt["statistik"]["schwelle"] == 3
    assert inhalt["ausschnitt"] == _beschreibung(tmp_path, "quelle")["ausschnitt"]
    quelle, bunt = tmp_path / "ausgabe" / "quelle", tmp_path / "ausgabe" / "bunt"
    assert (quelle / "roh.npy").read_bytes() == (bunt / "roh.npy").read_bytes()
    with Image.open(quelle / "bild.png") as a, Image.open(bunt / "bild.png") as b:
        assert not np.array_equal(np.asarray(a), np.asarray(b))


def test_faerbe_ohne_angaben_uebernimmt_die_einstellungen(tmp_path):
    assert main(["berechne", *SCHNELL, "--name", "quelle", "--schwelle", "4"]) == 0
    assert main(["faerbe", "ausgabe/quelle", "--name", "kopie"]) == 0
    quelle, kopie = _beschreibung(tmp_path, "quelle"), _beschreibung(tmp_path, "kopie")
    assert kopie["statistik"] == quelle["statistik"]
    assert kopie["palette"] == quelle["palette"]


def test_faerbe_eines_originals_erlaubt_nur_die_palette(tmp_path, org_daten, capsys):
    assert main(["original", str(org_daten / "M1.DAT")]) == 0
    assert main(["faerbe", "ausgabe/M1-palette1", "--palette", "0", "--name", "m1-weiss"]) == 0
    assert _beschreibung(tmp_path, "m1-weiss")["quelldatei"] == "M1.DAT"
    capsys.readouterr()
    assert main(["faerbe", "ausgabe/M1-palette1", "--schwelle", "5", "--name", "x"]) == 2
    assert "keine Abbruchwerte" in capsys.readouterr().err


def test_vergleiche_eine_datei(tmp_path, org_daten, capsys):
    assert main(["vergleiche", str(org_daten / "M1.DAT")]) == 0
    ausgabe = capsys.readouterr().out
    assert "M1.DAT" in ausgabe and "bestanden" in ausgabe and "NICHT" not in ausgabe
    ordner = tmp_path / "ausgabe" / "vergleich-M1"
    with Image.open(ordner / "vergleich.png") as png:
        assert png.size == (3 * 480 + 2 * 10, 480)
    inhalt = _beschreibung(tmp_path, "vergleich-M1")
    assert inhalt["quelldatei"] == "M1.DAT"
    assert inhalt["statistik"]["schwelle"] == 14
    assert inhalt["statistik"]["max_bereiche"] == 256
    assert inhalt["vergleich"]["bestanden"] is True
    assert inhalt["vergleich"]["menge"] >= 0.999


def test_vergleiche_meldet_verfehlte_grenze(org_daten, capsys):
    # Mit einer falschen Schwelle stimmen die Farbstufen nicht mehr.
    assert main(["vergleiche", str(org_daten / "M1.DAT"), "--schwelle", "500"]) == 1
    assert "NICHT bestanden" in capsys.readouterr().out


def test_vorhandener_lauf(tmp_path, capsys):
    assert main(["berechne", *SCHNELL, "--name", "doppelt"]) == 0
    capsys.readouterr()
    assert main(["berechne", *SCHNELL, "--name", "doppelt"]) == 2
    assert "existiert schon" in capsys.readouterr().err
    assert main(["berechne", *SCHNELL, "--name", "doppelt", "--ueberschreiben"]) == 0


@pytest.mark.parametrize(
    "befehl, stichwort",
    [
        (["berechne", "--xmin=1", "--xmax=0", "--ymin=0", "--ymax=1"], "xmin muss kleiner"),
        (["berechne", "--xmin=0", "--xmax=1", "--ymin=0"], "--ymax"),
        (["berechne", "--xmin=abc", "--xmax=1", "--ymin=0", "--ymax=1"], "keine Zahl"),
        (["berechne", *SCHNELL, "--palette", "7"], "Palette"),
        (["berechne", *SCHNELL, "--schwelle", "-3"], "Schwelle"),
        (["berechne", *SCHNELL, "--schwelle", "viel"], "Schwelle"),
        (["berechne", *SCHNELL, "--max-bereiche", "300"], "Höchstzahl"),
        (["berechne", *SCHNELL, "--name", "a/b"], "nicht erlaubt"),
        (["original", "gibt-es-nicht.DAT"], "gibt es nicht"),
        (["faerbe", "ausgabe/gibt-es-nicht"], "kein Lauf-Ordner"),
        (["vergleiche"], "Org_Daten"),
        (["tanze"], "Unbekannter Befehl"),
        ([], "Es fehlt"),
    ],
)
def test_falsche_eingaben_ergeben_rueckgabewert_2(befehl, stichwort, capsys):
    assert main(befehl) == 2
    meldung = capsys.readouterr().err
    assert meldung.startswith("Fehler: ")
    assert stichwort in meldung
