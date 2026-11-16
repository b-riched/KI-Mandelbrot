"""R6: Originaldateien lesen."""

import shutil

import numpy as np
import pytest

from mandelbrot.original import DATEIGROESSE, LESETABELLE, lies_dat
from mandelbrot.typen import Eingabefehler

# Datei -> (Faktor, Kopfzeile, Nachrechnung, höchste Farbstufe)
ERWARTET = {
    "M0.DAT": (1000, ("-2.099", "0.6", "-1.35", "1.35"),
               ("-2.1", "0.6", "-1.35", "1.35"), 258),
    "M01.DAT": (1000, ("-0.3", "0", "-0.9", "-0.6"),
                ("-0.3", "0", "-0.9", "-0.6"), 262),
    "M1.DAT": (1000, ("-0.429", "0.201", "-1.215", "-0.585"),
               ("-0.429", "0.201", "-1.215", "-0.585"), 256),
    "M11.DAT": (1000, ("-0.217", "-0.123", "-0.731", "-0.637"),
                ("-0.2175", "-0.1235", "-0.7317", "-0.6378"), 256),
    "M12.DAT": (10000, ("-0.1443", "-0.0504", "-1.0008", "-0.9063"),
                ("-0.1443", "-0.0504", "-1.0008", "-0.9063"), 256),
}


def _als_tupel(ausschnitt):
    text = ausschnitt.als_text()
    return (text["xmin"], text["xmax"], text["ymin"], text["ymax"])


def test_lesetabelle_kennt_genau_die_fuenf_originale():
    assert set(LESETABELLE) == set(ERWARTET)


@pytest.mark.parametrize("name", sorted(ERWARTET))
def test_original_lesen(org_daten, name):
    faktor, kopfzeile, nachrechnung, hoechste = ERWARTET[name]
    pfad = org_daten / name
    assert pfad.stat().st_size == DATEIGROESSE == 461760
    original = lies_dat(pfad)
    assert original.name == name
    assert original.faktor == faktor
    assert original.stufen.shape == (480, 480)
    assert original.stufen.dtype == np.int16
    assert original.stufen.min() == 0
    assert original.stufen.max() == hoechste
    assert _als_tupel(original.kopfzeile) == kopfzeile
    assert _als_tupel(original.nachrechnung) == nachrechnung


def test_falsche_dateigroesse(tmp_path):
    datei = tmp_path / "M0.DAT"
    datei.write_bytes(b"\0" * 1000)
    with pytest.raises(Eingabefehler, match="1000 Bytes"):
        lies_dat(datei)


def test_fehlende_datei(tmp_path):
    with pytest.raises(Eingabefehler, match="gibt es nicht"):
        lies_dat(tmp_path / "fehlt.DAT")


def test_unbekannte_datei_braucht_den_faktor(org_daten, tmp_path):
    kopie = tmp_path / "ANDERE.DAT"
    shutil.copyfile(org_daten / "M0.DAT", kopie)
    with pytest.raises(Eingabefehler, match="--faktor"):
        lies_dat(kopie)
    original = lies_dat(kopie, faktor=1000)
    assert original.regel is None
    assert _als_tupel(original.kopfzeile) == ("-2.099", "0.6", "-1.35", "1.35")
    assert original.nachrechnung == original.kopfzeile
