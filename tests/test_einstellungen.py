"""R17: Einstellungen und Ordner."""

import tomllib

import pytest

from conftest import REPO
from mandelbrot import einstellungen
from mandelbrot.typen import Eingabefehler


def test_standardwerte_ohne_datei(tmp_path):
    werte = einstellungen.lade(tmp_path)
    assert werte.projektordner == tmp_path
    assert werte.jobs == tmp_path / "_JOBS"
    assert werte.ergebnisse == tmp_path / "_ERGEBNISSE"
    assert werte.ereignisse == tmp_path / "_EVENTS"
    assert (werte.adresse, werte.port, werte.pause_sekunden) == ("0.0.0.0", 8000, 2.0)
    assert werte.ordner_fuer("neu") == tmp_path / "_JOBS" / "neu"
    with pytest.raises(ValueError):
        werte.ordner_fuer("irgendwo")


def test_datei_ueberschreibt_einzelne_werte(tmp_path):
    (tmp_path / "mandelbrot.toml").write_text(
        '[ordner]\nergebnisse = "Bilder"\n\n[server]\nport = 9000\n\n[arbeiter]\npause_sekunden = 0.5\n',
        encoding="utf-8",
    )
    werte = einstellungen.lade(tmp_path)
    assert werte.ergebnisse == tmp_path / "Bilder"
    assert werte.jobs == tmp_path / "_JOBS"  # nicht genannt, also Standard
    assert werte.port == 9000 and werte.pause_sekunden == 0.5


def test_pfad_ausserhalb_des_projektordners(tmp_path):
    woanders = tmp_path / "woanders"
    projekt = tmp_path / "projekt"
    projekt.mkdir()
    (projekt / "mandelbrot.toml").write_text(
        f"[ordner]\nergebnisse = '{woanders.as_posix()}'\n", encoding="utf-8"
    )
    assert einstellungen.lade(projekt).ergebnisse == woanders


@pytest.mark.parametrize(
    "inhalt, stichwort",
    [
        ("[drucker]\nname = 'x'\n", "[drucker]"),
        ("[server]\nprot = 8000\n", "prot"),
        ("[server]\nport = 0\n", "port"),
        ("[server]\nport = 'achttausend'\n", "port"),
        ("[server]\nadresse = 5\n", "adresse"),
        ("[arbeiter]\npause_sekunden = 0\n", "pause_sekunden"),
        ("[ordner]\njobs = 7\n", "jobs"),
        ("[ordner\njobs = 'x'\n", "nicht lesbar"),
    ],
)
def test_fehler_in_der_datei(tmp_path, inhalt, stichwort):
    (tmp_path / "mandelbrot.toml").write_text(inhalt, encoding="utf-8")
    with pytest.raises(Eingabefehler, match=r".*" + stichwort.replace("[", r"\[").replace("]", r"\]")):
        einstellungen.lade(tmp_path)


def test_ordner_werden_angelegt(tmp_path):
    werte = einstellungen.lade(tmp_path)
    einstellungen.lege_ordner_an(werte)
    einstellungen.lege_ordner_an(werte)  # ein zweites Mal schadet nicht
    for stand in einstellungen.STAENDE:
        assert (tmp_path / "_JOBS" / stand).is_dir()
    assert (tmp_path / "_ERGEBNISSE").is_dir() and (tmp_path / "_EVENTS").is_dir()


def test_vorlage_im_repo_entspricht_den_standardwerten(tmp_path):
    vorlage = (REPO / "mandelbrot.beispiel.toml").read_text(encoding="utf-8")
    assert tomllib.loads(vorlage) == einstellungen._STANDARD
    ohne_datei = einstellungen.lade(tmp_path)
    (tmp_path / "mandelbrot.toml").write_text(vorlage, encoding="utf-8")
    assert einstellungen.lade(tmp_path) == ohne_datei
