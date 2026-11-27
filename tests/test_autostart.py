"""R26: Autostart unter Windows. Der Autostart-Ordner liegt im Test im temporären Ordner."""

import sys

import pytest

from mandelbrot import autostart
from mandelbrot.kommandozeile import main
from mandelbrot.typen import Eingabefehler

PROJEKT = r"X:\privat Richard\eigene Programme\Fraktales\KI-Mandel"
PYTHON = PROJEKT + r"\.venv\Scripts\python.exe"


def _windows(tmp_path):
    return {"umgebung": {"APPDATA": str(tmp_path)}, "system": "win32"}


def test_pfad_der_autostart_datei(tmp_path):
    datei = autostart.datei(**_windows(tmp_path))
    assert datei.name == "KI-Mandelbrot.cmd"
    assert datei.parent == tmp_path / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


@pytest.mark.parametrize("system", ["linux", "darwin"])
def test_nur_unter_windows(tmp_path, system):
    with pytest.raises(Eingabefehler, match="nur unter Windows"):
        autostart.datei({"APPDATA": str(tmp_path)}, system)


def test_ohne_appdata(tmp_path):
    with pytest.raises(Eingabefehler, match="APPDATA"):
        autostart.datei({}, "win32")


def test_an_und_aus(tmp_path):
    windows = _windows(tmp_path)
    assert not autostart.ist_an(**windows)
    datei = autostart.schalte_an(PROJEKT, PYTHON, **windows)
    assert autostart.ist_an(**windows) and datei.is_file()
    assert autostart.schalte_aus(**windows) is True
    assert not autostart.ist_an(**windows) and not datei.exists()
    assert autostart.schalte_aus(**windows) is False


def test_inhalt_der_autostart_datei(tmp_path):
    datei = autostart.schalte_an(PROJEKT, PYTHON, **_windows(tmp_path))
    roh = datei.read_bytes()
    assert b"\r\n" in roh and roh.count(b"\n") == roh.count(b"\r\n")  # Zeilenenden von Windows
    zeilen = roh.decode("utf-8").split("\r\n")
    assert zeilen[0] == "@echo off"
    assert f'cd /d "{PROJEKT}"' in zeilen
    assert f'"{PYTHON}" -m mandelbrot start' in zeilen
    # Die Datei wartet, bis das Netzlaufwerk verbunden ist.
    assert f'if not exist "{PROJEKT}\\" (' in zeilen
    assert zeilen.index(":warten") < zeilen.index(f'cd /d "{PROJEKT}"')


def test_zweimal_anschalten_ersetzt_die_datei(tmp_path):
    windows = _windows(tmp_path)
    autostart.schalte_an("C:\\alt", PYTHON, **windows)
    datei = autostart.schalte_an(PROJEKT, PYTHON, **windows)
    text = datei.read_text(encoding="utf-8")
    assert "C:\\alt" not in text and PROJEKT in text


# ------------------------------------------------------------- der Befehl


@pytest.fixture
def als_windows(tmp_path, monkeypatch):
    """Lässt den Befehl glauben, er liefe unter Windows. Der echte Autostart-Ordner bleibt unberührt."""
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("APPDATA", str(tmp_path / "appdata"))
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_befehl_autostart(als_windows, capsys):
    assert main(["autostart"]) == 0
    assert "ist aus" in capsys.readouterr().out
    assert main(["autostart", "an"]) == 0
    assert "ist an" in capsys.readouterr().out
    datei = autostart.datei()
    text = datei.read_text(encoding="utf-8")
    assert f'cd /d "{als_windows}"' in text and "-m mandelbrot start" in text
    assert main(["autostart"]) == 0
    assert "ist an" in capsys.readouterr().out
    assert main(["autostart", "aus"]) == 0
    assert not datei.exists()
    assert main(["autostart", "aus"]) == 0
    assert "war schon aus" in capsys.readouterr().out


def test_befehl_autostart_mit_falschem_schalter(als_windows, capsys):
    assert main(["autostart", "vielleicht"]) == 2
    assert "'an' oder 'aus'" in capsys.readouterr().err


def test_befehl_autostart_auf_anderem_betriebssystem(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "platform", "linux")
    assert main(["autostart", "an"]) == 2
    assert "nur unter Windows" in capsys.readouterr().err
