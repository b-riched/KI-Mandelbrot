"""Von Farbstufen zum Bild (R5), portiert aus MANDELFA.PAS."""

from __future__ import annotations

import numpy as np
from PIL import Image


def bild(stufen: np.ndarray, palette: np.ndarray) -> Image.Image:
    """Färbt Farbstufen ein. Stufen über 255 bekommen die Palettenfarbe 255.

    Bildlage wie 1991: Spalte 1 links, Zeile 1 oben.
    """
    index = np.clip(stufen, 0, 255)
    rgb = palette[index]  # Form (Spalten, Zeilen, 3)
    return Image.fromarray(np.ascontiguousarray(rgb.transpose(1, 0, 2)))
