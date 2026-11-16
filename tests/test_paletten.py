"""R4 und R5: Paletten und Einfärben."""

import numpy as np
import pytest

from mandelbrot.einfaerben import bild
from mandelbrot.paletten import palette
from mandelbrot.typen import Eingabefehler

# Kontrollwerte aus der technischen Spec: Farbe -> (Rot, Grün, Blau)
KONTROLLWERTE = {
    0: {16: (32, 32, 162), 64: (194, 194, 255), 96: (255, 255, 255),
        144: (255, 255, 255), 255: (255, 255, 255)},
    1: {16: (0, 0, 65), 64: (65, 0, 255), 96: (194, 0, 194),
        144: (255, 0, 0), 255: (255, 255, 0)},
    2: {16: (65, 0, 0), 64: (255, 65, 0), 96: (255, 255, 65),
        144: (0, 0, 0), 255: (0, 0, 0)},
}
KONTROLLWERTE[3] = KONTROLLWERTE[1]


@pytest.mark.parametrize("nummer", [0, 1, 2, 3])
def test_form_typ_und_kontrollwerte(nummer):
    farben = palette(nummer)
    assert farben.shape == (256, 3)
    assert farben.dtype == np.uint8
    assert tuple(farben[0]) == (0, 0, 0)
    for farbe, erwartet in KONTROLLWERTE[nummer].items():
        assert tuple(int(wert) for wert in farben[farbe]) == erwartet, farbe


def test_palette_3_ist_palette_1():
    assert np.array_equal(palette(1), palette(3))


def test_flaechen_wie_im_original():
    assert (palette(0)[88:] == 255).all()  # ab Farbe 88 Weiß
    assert (palette(1)[208:] == (255, 255, 0)).all()  # ab Farbe 208 Gelb
    assert (palette(2)[113:] == 0).all()  # ab Farbe 113 Schwarz


def test_unbekannte_palette():
    with pytest.raises(Eingabefehler):
        palette(4)


def test_bildlage_und_stufen_ueber_255():
    stufen = np.zeros((480, 480), np.int16)
    stufen[10, 20] = 5  # Spalte 11, Zeile 21
    stufen[30, 40] = 262  # kommt nur in Originaldateien vor
    farben = palette(1)
    ergebnis = bild(stufen, farben)
    assert ergebnis.size == (480, 480) and ergebnis.mode == "RGB"
    assert ergebnis.getpixel((10, 20)) == tuple(int(w) for w in farben[5])
    assert ergebnis.getpixel((30, 40)) == tuple(int(w) for w in farben[255])
    assert ergebnis.getpixel((0, 0)) == (0, 0, 0)
