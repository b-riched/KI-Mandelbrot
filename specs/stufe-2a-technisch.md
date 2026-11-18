# Stufe 2a: Bildgrößen und freier Ausschnitt – technische Spec

Status: freigegeben von Thorsten am 16.11.2026. Richard gibt mit der Übernahme des Pull Requests frei.
Stand: 16.11.2026, beim Bauen an vier Stellen präzisiert, siehe „Präzisierungen beim Bauen"
Übergeordnet: [Stufenkonzept](stufenkonzept.md)
Gegenstück: [fachliche Spec](stufe-2a-fachlich.md)
Baut auf: [technische Spec Stufe 1](stufe-1-technisch.md)

Diese Spec beschreibt nur, was sich gegenüber Stufe 1 ändert. Die Regeln
R9 bis R16 und die Abnahmekriterien B1 bis B9 stehen in der fachlichen
Spec.

## Rahmen

Unverändert: Python 3.12, `numpy`, `pillow`, `pytest`, Rechnen mit NumPy
und `float64` auf dem Prozessor. Es kommt keine neue Abhängigkeit dazu.

Leitlinie: Kein Test aus Stufe 1 wird geändert. Alle müssen weiter
durchlaufen.

## Geänderte und neue Dateien

| Datei | Änderung |
| --- | --- |
| `src/mandelbrot/typen.py` | neu: `Bildausschnitt`, `GROESSEN`, `lies_groesse` |
| `src/mandelbrot/berechnen.py` | neu: `rechne`, `koordinaten`, `berechne_bild`. `abbruchwerte` ruft `rechne` auf |
| `src/mandelbrot/statistik.py` | alle Funktionen bekommen den Parameter `grenze`. Schnellere Fassung von `bereichsbreiten` und `automatische_schwelle` |
| `src/mandelbrot/ablage.py` | Format 2, `glatt.npy`, Zahlentyp von `roh.npy` |
| `src/mandelbrot/kommandozeile.py` | `berechne` mit zweiter Form und `--abbruchgrenze` |
| `tests/test_bildausschnitt.py` | neu |
| `tests/test_rechne.py` | neu |
| `tests/test_statistik_grenze.py` | neu |
| `tests/test_kommandozeile_2a.py` | neu |
| `tests/test_abnahme_2a.py` | neu |

`einfaerben.py`, `paletten.py`, `original.py` und `vergleich.py` bleiben
unverändert.

## Datenmodell

Felder mit Bildpunkten haben die Form `(B, H)` und werden wie in Stufe 1
mit `[Spalte − 1, Zeile − 1]` angesprochen. Zeile 1 ist oben.

| Feld | Typ | Werte |
| --- | --- | --- |
| Abbruchwerte | `int32` aus `rechne`, in der Datei siehe unten | 1 bis Abbruchgrenze + 1 |
| gebrochene Abbruchwerte | `float32` | für Punkte der Menge 0, ohne Bedeutung |
| Farbstufen | `int16` | 0 bis 256 |

### typen.py

```python
GROESSEN = {"hd": (1280, 720), "fullhd": (1920, 1080),
            "wqhd": (2560, 1440), "ipad": (2360, 1640)}
SEITE_MIN, SEITE_MAX = 16, 10_000
GRENZE_MIN, GRENZE_MAX = 10, 1_000_000

@dataclass(frozen=True)
class Bildausschnitt:
    mitte_x: Decimal
    mitte_y: Decimal
    breite: Decimal          # Bildbreite in der Zahlenebene, größer als 0
    pixel_b: int             # Breite in Bildpunkten
    pixel_h: int             # Höhe in Bildpunkten
```

- `lies_groesse(text)` nimmt einen Namen aus `GROESSEN` oder `BREITExHÖHE`
  an, Groß- und Kleinschreibung egal, als Trennzeichen `x` oder `×`.
- `Bildausschnitt.aus_text(...)` prüft alle Grenzen und meldet Fehler als
  `Eingabefehler`.

## Algorithmen

### Koordinaten (R10, R11, R15)

```python
def koordinaten(bild):
    a = float(bild.breite / bild.pixel_b)
    mx, my = float(bild.mitte_x), float(bild.mitte_y)
    cx = mx + (np.arange(bild.pixel_b) - (bild.pixel_b - 1) / 2) * a
    cy = my - (np.arange(bild.pixel_h) - (bild.pixel_h - 1) / 2) * a
    return cx, cy, a
```

Der Punktabstand wird als Dezimalzahl geteilt und erst dann in `float`
umgewandelt.

Prüfung nach R15, je Achse:

- Feinheit ist `np.spacing` des größten Betrags im Vektor.
- Fehler, wenn nicht alle Werte des Vektors verschieden sind.
- Warnung, wenn `a < 4 * Feinheit` oder die Bildbreite unter `1e-12` liegt.

Warnungen gehen als Liste an den Aufrufer. Die Kommandozeile schreibt sie
mit dem Wort `Warnung:` auf die Fehlerausgabe. Der Rückgabewert bleibt 0.

### Rechenkern

```python
def rechne(cx, cy, grenze, block=64):
    B, H = len(cx), len(cy)
    roh = np.full((B, H), grenze + 1, np.int32)
    glatt = np.zeros((B, H), np.float32)
    for a in range(0, B, block):
        b = min(a + block, B)
        px = np.repeat(cx[a:b], H)
        py = np.tile(cy, b - a)
        idx = np.arange((b - a) * H)
        zx = np.zeros(idx.size)
        zy = np.zeros(idx.size)
        roh_b = roh[a:b].reshape(-1)
        glatt_b = glatt[a:b].reshape(-1)
        for schritt in range(1, grenze + 2):
            hx = zx * zx - zy * zy + px
            hy = 2 * zx * zy + py
            zx, zy = hx, hy
            r2 = zx * zx + zy * zy
            raus = r2 >= 4
            if raus.any():
                if schritt <= grenze:
                    roh_b[idx[raus]] = schritt
                    glatt_b[idx[raus]] = _gebrochen(
                        zx[raus], zy[raus], px[raus], py[raus], r2[raus], schritt)
                bleibt = ~raus
                idx, px, py = idx[bleibt], px[bleibt], py[bleibt]
                zx, zy = zx[bleibt], zy[bleibt]
                if idx.size == 0:
                    break
    return roh, glatt
```

- Die Rechenschritte für `hx` und `hy` sind dieselben wie in Stufe 1. Für
  gleiche Koordinaten kommen deshalb dieselben Abbruchwerte heraus.
- Neu ist nur die Buchführung: Gerechnet wird blockweise über 64 Spalten,
  und abgebrochene Punkte werden aus den Feldern entfernt. Das spart
  Rechenzeit und Speicher.
- Ein Punkt, der erst im Schritt `grenze + 1` abbricht, zählt wie in Stufe 1
  zur Menge.
- `abbruchwerte(ausschnitt, raster, grenze)` aus Stufe 1 behält Aufruf und
  Ergebnis. Es bildet die Vektoren nach R1 und ruft `rechne` auf.
- `berechne_bild(bild, grenze)` bildet die Vektoren nach R10 und gibt
  Abbruchwerte, gebrochene Abbruchwerte und Warnungen zurück.

### Gebrochene Abbruchwerte (R13)

```python
def _gebrochen(zx, zy, px, py, r2, schritt):
    schritte = np.full(zx.size, float(schritt))
    for _ in range(8):
        klein = r2 < 65536.0
        if not klein.any():
            break
        hx = zx * zx - zy * zy + px
        hy = 2 * zx * zy + py
        zx = np.where(klein, hx, zx)
        zy = np.where(klein, hy, zy)
        schritte += klein
        r2 = zx * zx + zy * zy
    return schritte + 1 - np.log2(0.5 * np.log(r2))
```

Nach dem Abbruch wird höchstens 8 Schritte weitergerechnet, bis der Betrag
von z mindestens 256 ist. Der Wert ist `Schritte + 1 − log2(ln |z|)`. Das
ist die übliche Formel für stufenlose Abbruchwerte.

### statistik.py (R14)

Alle Funktionen bekommen `grenze` als letzten Parameter mit dem Standard
1005. Die Regeln bleiben, überall steht `grenze` an der Stelle von 1005.

Zwei Funktionen werden schneller, ohne ihr Ergebnis zu ändern:

- `bereichsbreiten` durchläuft bei einer Schwelle ab 1 nur die Abbruchwerte,
  die im Bild vorkommen. Werte ohne Bildpunkte können nie einen Bereich
  schließen. Bei Schwelle 0 hat jeder Abbruchwert die Breite 1.
- `automatische_schwelle` sucht per Halbierung zwischen 1 und der Zahl der
  Bildpunkte außerhalb der Menge. Das ist zulässig, weil die Zahl der
  Bereiche mit wachsender Schwelle nie steigt.

Die Fassungen aus Stufe 1 wandern als Vergleichsmaßstab in die Tests.

### ablage.py (R16)

| Datei | Inhalt | Vorhanden bei |
| --- | --- | --- |
| `roh.npy` | Abbruchwerte, `int16` bis Abbruchgrenze 32.766, darüber `int32` | berechneten Läufen |
| `glatt.npy` | gebrochene Abbruchwerte, `float32` | berechneten Läufen nach R10 |
| `stufen.npy`, `bild.png`, `lauf.json` | wie Stufe 1 | allen Läufen |

`lauf.json` bekommt `"format": 2`. Für die neue Form:

```json
{
  "format": 2,
  "herkunft": "berechnet",
  "bild": {
    "mitte_x": "-0.75",
    "mitte_y": "0",
    "breite": "3.5",
    "lage": "aufrecht"
  },
  "raster": [1920, 1080],
  "abbruchgrenze": 1005,
  "wert_in_menge": 1006
}
```

- Das Beispiel zeigt nur die neuen und geänderten Angaben.
- Läufe nach R1 behalten `ausschnitt` und bekommen dazu
  `"lage": "wie 1991"` auf oberster Ebene. `bild` fehlt dort.
- `lies_lauf` liest Format 1 und Format 2. Ein Lauf im Format 1 gilt als
  Lauf nach R1 mit Abbruchgrenze 1005.
- `faerbe` übernimmt `bild` oder `ausschnitt` vom Ausgangslauf und kopiert
  `glatt.npy`, wenn vorhanden.

## Kommandozeile

```
python -m mandelbrot berechne --mitte-x=-0.75 --mitte-y=0 --breite=3.5 --groesse fullhd --name gesamt-hd
python -m mandelbrot berechne --mitte-x=-0.7436 --mitte-y=0.1318 --breite=0.002 --groesse 800x600 --abbruchgrenze 5000
python -m mandelbrot berechne --xmin=-2.1 --xmax=0.6 --ymin=-1.35 --ymax=1.35
```

Neue Optionen von `berechne`:

| Option | Bedeutung |
| --- | --- |
| `--mitte-x`, `--mitte-y` | Mittelpunkt, Dezimalzahl mit Punkt oder Komma |
| `--breite` | Bildbreite in der Zahlenebene, größer als 0 |
| `--groesse` | Name oder `BREITExHÖHE`, Pflicht in der neuen Form |
| `--abbruchgrenze` | 10 bis 1.000.000, Standard 1005, in beiden Formen erlaubt |

Regeln:

- Wer Optionen beider Formen mischt, bekommt einen Fehler mit
  Rückgabewert 2. Dasselbe gilt, wenn in der neuen Form eine der vier
  Angaben fehlt.
- `faerbe` und `vergleiche` bekommen keine neuen Optionen. `faerbe` liest
  die Abbruchgrenze aus dem Ausgangslauf.

## Tests

| Test | Prüft | Kriterium |
| --- | --- | --- |
| `test_bildausschnitt` | Namen und freie Größen, Grenzen, Fehlermeldungen. Mittelpunkt in der Bildmitte bei gerader und ungerader Größe. Gleicher Punktabstand in beiden Richtungen. Zeile 1 hat die größte y-Koordinate. Warnung und Fehler nach R15 an gemessenen Beispielen. | R9, R10, R11, R15, B2, B6 |
| `test_rechne` | Gleichheit mit der Schleife von Hand an kleinen Rastern. Gleichheit mit dem Ergebnis aus Stufe 1 für zwei Ausschnitte der Lesetabelle. Ergebnis unabhängig von der Blockgröße. Gebrochene Werte: endlich, für Punkte der Menge 0, und benachbarte Punkte weit außerhalb der Menge unterscheiden sich um weniger als 1. | R12, R13, B3, B7 |
| `test_statistik_grenze` | Schnelle Fassungen liefern für zufällige Häufigkeiten dasselbe wie die Fassungen aus Stufe 1, auch mit Schwelle 0 und mit anderer Grenze. Summe der Breiten ist die Abbruchgrenze. | R14, B4 |
| `test_kommandozeile_2a` | Neue Form mit Name und freier Größe. Mischen der Formen und fehlende Angaben ergeben Rückgabewert 2. `--abbruchgrenze` in beiden Formen. `faerbe` auf einem neuen Lauf. Lesen eines Laufs im Format 1. | R16, B1 |
| `test_abnahme_2a` | Die vier benannten Größen und eine freie, jeweils mit Prüfung der Größe des PNG. Ein Bild mit Abbruchgrenze 5000. Rechenzeiten werden ausgegeben. | B1, B4, B8 |

Die Tests aus Stufe 1 laufen unverändert mit. Richtwert für die gesamte
Laufzeit: unter 3 Minuten.

B5 ist kein automatischer Test. Das Bild wird mit einem Befehl gerechnet,
der mit Stufe 2a ins README kommt, und von Richard angesehen.

## Rechenzeiten

Gemessen auf dem Prozessor mit der Ansicht der ganzen Menge (Mittelpunkt
−0,75 / 0, Bildbreite 3,5) und Abbruchgrenze 1005. Die Spalte „beim Bauen"
stammt aus der Bauumgebung am 16.11.2026. Die Spalte „Richards PC" hat
Richard am 18.11.2026 gemessen
(`docs/abnahme-stufe-2a--rechenzeiten.txt`). Der Test `test_abnahme_2a` misst
die Zeiten bei jedem Lauf neu und schreibt sie nach
`ausgabe/abnahme-b1/rechenzeiten.txt`.

| Bildgröße | Voranalyse | Gemessen beim Bauen | Richards PC |
| --- | --- | --- | --- |
| `hd` 1280 × 720 | 1,1 s | 1,4 s | 1,1 s |
| `fullhd` 1920 × 1080 | | 3,3 s | 2,4 s |
| `wqhd` 2560 × 1440 | 4,7 s | 6,6 s | 4,5 s |
| `ipad` 2360 × 1640 | | 5,3 s | 3,6 s |

Das tiefe Bild für B5 (10⁻¹² Bildbreite, 2560 × 1440, Abbruchgrenze 5000)
brauchte beim Bauen 57 Sekunden. In den Abbruchwerten gibt es keine zwei
gleichen Nachbarspalten oder Nachbarzeilen.

## Zuordnung von Abnahme und Nachweis

| Kriterium | Nachweis |
| --- | --- |
| B1 | `test_abnahme_2a`, Bilder in `ausgabe/abnahme-b1/` |
| B2 | `test_bildausschnitt` |
| B3 | alle Tests aus Stufe 1, `python -m mandelbrot vergleiche` |
| B4 | `test_statistik_grenze`, `test_abnahme_2a` |
| B5 | Befehl aus dem README, Richard sieht das Bild an |
| B6 | `test_bildausschnitt` |
| B7 | `test_rechne`, `test_kommandozeile_2a` |
| B8 | Tabelle „Rechenzeiten" in dieser Spec |
| B9 | `git tag stufe-2a` nach der Abnahme |

## Präzisierungen beim Bauen

Beim Bauen am 16.11.2026 wurde diese Spec an vier Stellen genauer gefasst.

1. Gebrochene Abbruchwerte gibt es nur für Bilder nach R10. Die Form wie
   1991 schreibt kein `glatt.npy`. Sonst hätte ein Test aus Stufe 1
   geändert werden müssen, und das schließt die Leitlinie aus.
2. `stufentabelle` bekommt keinen Parameter `grenze`. Die Abbruchgrenze
   ergibt sich aus der Summe der Breiten.
3. Die Warnung nach R15 ist entweder die Warnung zur Bildbreite oder die
   zum Punktabstand, nie beide zugleich.
4. Die Versionsnummer des Pakets ist 0.2.0.

Punkt T5 ist erledigt: Das Bild für B5 rechnet auf dem Prozessor in etwa
einer Minute und bleibt in Stufe 2a.

## Nicht in dieser Stufe

- Numba, CUDA und die Wahl zwischen Prozessor und Grafikkarte (Stufe 2b).
- Mehrere Prozessorkerne.
- Das Format von Job-Dateien (Stufe 3).
- Farben aus `glatt.npy` (Stufe 5).

## Offene technische Punkte

| Nr. | Frage | Vorschlag |
| --- | --- | --- |
| T4 | Soll Stufe 2a auf dem Branch von Stufe 1 aufbauen, solange Stufe 1 nicht gemergt ist? | Ja. Der Pull Request für 2a wird erst nach dem Merge von Stufe 1 angelegt. |
| T5 | Wie lange darf das Bild für B5 rechnen? | Erledigt: 57 Sekunden beim Bauen. B5 bleibt in Stufe 2a. |
