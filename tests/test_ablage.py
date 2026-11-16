"""R8: Lauf-Ordner schreiben und lesen."""

import json

import numpy as np
import pytest
from PIL import Image

from mandelbrot import ablage
from mandelbrot.einfaerben import bild
from mandelbrot.paletten import palette
from mandelbrot.typen import Ausschnitt, Eingabefehler

LANG = "-0.743643887037158704752191506114774"  # 33 Nachkommastellen


def _beispiel():
    rng = np.random.default_rng(7)
    roh = rng.integers(1, 1007, (480, 480)).astype(np.int16)
    stufen = (roh % 256).astype(np.int16)
    ausschnitt = Ausschnitt.aus_text(LANG, "-0,7436438870371587047521915061147", "0.1", "0.2")
    angaben = ablage.beschreibung("berechnet", ausschnitt, 1)
    angaben["statistik"] = {"schwelle": 5, "breiten": [1, 2, 3]}
    return roh, stufen, angaben


def _schreibe(ordner, **mehr):
    roh, stufen, angaben = _beispiel()
    return ablage.schreibe_lauf(
        ordner,
        beschreibung=angaben,
        stufen=stufen,
        bild=bild(stufen, palette(1)),
        roh=roh,
        **mehr,
    )


def test_schreiben_und_lesen(tmp_path):
    roh, stufen, _ = _beispiel()
    ordner = _schreibe(tmp_path / "probe")
    assert sorted(p.name for p in ordner.iterdir()) == [
        "bild.png", "lauf.json", "roh.npy", "stufen.npy",
    ]
    lauf = ablage.lies_lauf(ordner)
    assert np.array_equal(lauf.roh, roh) and lauf.roh.dtype == np.int16
    assert np.array_equal(lauf.stufen, stufen)
    assert lauf.beschreibung["herkunft"] == "berechnet"
    assert lauf.beschreibung["raster"] == [480, 480]
    assert lauf.beschreibung["abbruchgrenze"] == 1005
    assert lauf.beschreibung["wert_in_menge"] == 1006
    with Image.open(ordner / "bild.png") as png:
        assert png.size == (480, 480) and png.mode == "RGB"


def test_koordinaten_bleiben_als_text_erhalten(tmp_path):
    ordner = _schreibe(tmp_path / "probe")
    text = (ordner / "lauf.json").read_text(encoding="utf-8")
    inhalt = json.loads(text)
    assert inhalt["ausschnitt"]["xmin"] == LANG
    # Das Komma wird zum Punkt, sonst ändert sich nichts.
    assert inhalt["ausschnitt"]["xmax"] == "-0.7436438870371587047521915061147"
    assert ablage.ausschnitt_aus(inhalt).als_text() == inhalt["ausschnitt"]
    # Zahlenlisten stehen in einer Zeile.
    assert '"breiten": [1, 2, 3]' in text
    assert '"raster": [480, 480]' in text


def test_vorhandener_lauf_wird_nicht_stillschweigend_ersetzt(tmp_path):
    ordner = _schreibe(tmp_path / "probe")
    (ordner / "notiz.txt").write_text("bleibt", encoding="utf-8")
    with pytest.raises(Eingabefehler, match="existiert schon"):
        _schreibe(ordner)
    assert (ordner / "notiz.txt").exists()
    _schreibe(ordner, ueberschreiben=True)
    assert not (ordner / "notiz.txt").exists()


def test_gleiche_eingaben_ergeben_gleiche_dateien(tmp_path):
    eins = _schreibe(tmp_path / "eins")
    zwei = _schreibe(tmp_path / "zwei")
    for name in ("roh.npy", "stufen.npy"):
        assert (eins / name).read_bytes() == (zwei / name).read_bytes()
    with Image.open(eins / "bild.png") as a, Image.open(zwei / "bild.png") as b:
        assert np.array_equal(np.asarray(a), np.asarray(b))


def test_kein_lauf_ordner(tmp_path):
    with pytest.raises(Eingabefehler, match="kein Lauf-Ordner"):
        ablage.lies_lauf(tmp_path)


@pytest.mark.parametrize("name", ["", "..", "a/b", "a:b"])
def test_unerlaubte_namen(name):
    with pytest.raises(Eingabefehler):
        ablage.pruefe_name(name)


def test_ungueltiger_ausschnitt():
    with pytest.raises(Eingabefehler, match="xmin muss kleiner"):
        Ausschnitt.aus_text("1", "0", "0", "1")
    with pytest.raises(Eingabefehler, match="keine Zahl"):
        Ausschnitt.aus_text("abc", "0", "0", "1")
