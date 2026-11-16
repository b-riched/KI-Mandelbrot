"""Gemeinsame Hilfen für alle Tests."""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ORG_DATEN = REPO / "Org_Daten"
ORIGINALE = ("M0.DAT", "M01.DAT", "M1.DAT", "M11.DAT", "M12.DAT")


@pytest.fixture
def org_daten() -> Path:
    return ORG_DATEN
