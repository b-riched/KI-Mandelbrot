"""Korrektur F-01 aus der Abnahme von Stufe 1.

Die Angabe eines Faktors gilt nur für Dateien, die nicht in der Lesetabelle
stehen. Bei den fünf Originalen ist der Faktor fest.
"""

import shutil

import pytest

from conftest import ORIGINALE
from mandelbrot.kommandozeile import main
from mandelbrot.original import LESETABELLE, lies_dat
from mandelbrot.typen import Eingabefehler


@pytest.mark.parametrize("name", ORIGINALE)
@pytest.mark.parametrize("faktor", [2000, "tabelle"])
def test_faktor_wird_bei_dateien_der_lesetabelle_abgelehnt(org_daten, name, faktor):
    # Auch der richtige Faktor wird abgelehnt: Die Regel soll einfach sein.
    faktor = LESETABELLE[name].faktor if faktor == "tabelle" else faktor
    with pytest.raises(Eingabefehler, match="steht in der Lesetabelle"):
        lies_dat(org_daten / name, faktor=faktor)


def test_ohne_faktor_bleibt_alles_wie_bisher(org_daten):
    original = lies_dat(org_daten / "M0.DAT")
    assert original.faktor == 1000
    assert original.kopfzeile.als_text()["xmin"] == "-2.099"
    assert original.nachrechnung.als_text()["xmin"] == "-2.1"


def test_schreibweise_des_dateinamens_spielt_keine_rolle(org_daten, tmp_path):
    kopie = tmp_path / "m0.dat"
    shutil.copyfile(org_daten / "M0.DAT", kopie)
    with pytest.raises(Eingabefehler, match="steht in der Lesetabelle"):
        lies_dat(kopie, faktor=2000)


def test_unbekannte_datei_nimmt_den_faktor_weiter_an(org_daten, tmp_path):
    kopie = tmp_path / "ANDERE.DAT"
    shutil.copyfile(org_daten / "M0.DAT", kopie)
    assert lies_dat(kopie, faktor=2000).kopfzeile.als_text()["xmin"] == "-1.0495"


def test_befehl_original_lehnt_den_faktor_ab(org_daten, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["original", str(org_daten / "M0.DAT"), "--faktor", "2000"]) == 2
    meldung = capsys.readouterr().err
    assert meldung.startswith("Fehler: ") and "der Faktor 1000 ist fest" in meldung
    assert not (tmp_path / "ausgabe").exists()
    assert main(["original", str(org_daten / "M0.DAT")]) == 0
