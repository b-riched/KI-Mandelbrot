# Stufe 1: Portierung – technische Spec

Status: freigegeben von Thorsten am 16.11.2026. Richard gibt mit der Übernahme des Pull Requests frei.
Stand: 16.11.2026, beim Bauen an sechs Stellen präzisiert, siehe „Präzisierungen beim Bauen"
Übergeordnet: [Stufenkonzept](stufenkonzept.md)
Gegenstück: [fachliche Spec](stufe-1-fachlich.md)

Diese Spec beschreibt, **wie** die fachliche Spec umgesetzt wird. Die
Regeln R1 bis R8 und die Abnahmekriterien A1 bis A8 stehen dort und werden
hier nur zitiert.

## Rahmen

| Thema | Festlegung |
| --- | --- |
| Sprache | Python 3.12 |
| Abhängigkeiten | `numpy`, `pillow`, `pytest` (stehen schon in `requirements.txt`). Dazu kommt dort die Zeile `-e .`, die das Paket selbst einrichtet, damit `python -m mandelbrot` funktioniert. |
| Rechnen | NumPy auf dem Prozessor, Zahlentyp `float64` |
| Paket | `src/mandelbrot/`, Aufruf mit `python -m mandelbrot` |
| Tests | `tests/`, Aufruf mit `python -m pytest` |
| Ausgabe | `ausgabe/<Name>/`, von Git ignoriert |

Nicht verwendet werden in dieser Stufe: Numba, CUDA, mehrere Prozesse,
eine Datenbank, ein Webserver.

## Dateien, die in Stufe 1 entstehen

```
pyproject.toml
src/mandelbrot/
├── __init__.py       Versionsnummer
├── __main__.py       ruft kommandozeile.main() auf
├── typen.py          Ausschnitt, Lauf
├── berechnen.py      R1, R2
├── statistik.py      R3
├── paletten.py       R4
├── einfaerben.py     R5
├── original.py       R6: .DAT lesen, Lesetabelle
├── vergleich.py      R7
├── ablage.py         R8: Lauf-Ordner lesen und schreiben
└── kommandozeile.py  Befehle
tests/
├── conftest.py      Pfade zum Repo und zu Org_Daten
├── test_berechnen.py
├── test_statistik.py
├── test_paletten.py
├── test_original.py
├── test_ablage.py
├── test_kommandozeile.py
└── test_abnahme.py   A1 bis A3 gegen Org_Daten
```

Die Platzhalter `src/mandelbrot/.gitkeep` und `tests/.gitkeep` entfallen.

`pyproject.toml` legt nur das Nötige fest: Paketname `ki-mandelbrot`,
Version `0.1.0`, Quellordner `src`, Python ab 3.12, und für pytest
`testpaths = ["tests"]` und `pythonpath = ["src"]`. Damit laufen die Tests
auch ohne Installation des Pakets.

## Datenmodell

### Felder und ihre Lage

Alle Felder mit Bildpunkten haben die Form `(480, 480)` und werden mit
`[x − 1, y − 1]` angesprochen: erster Index Spalte, zweiter Index Zeile. Das
ist dieselbe Reihenfolge wie in den `.DAT`-Dateien, in denen jeder Datensatz
eine Spalte ist.

| Feld | Typ | Werte |
| --- | --- | --- |
| Abbruchwerte | `int16` | 1 bis 1006 |
| Farbstufen | `int16` | 0 bis 256, in Originaldateien bis 262 |
| Palette | `uint8`, Form `(256, 3)` | Rot, Grün, Blau je 0 bis 255 |

### typen.py

```python
@dataclass(frozen=True)
class Ausschnitt:
    xmin: Decimal
    xmax: Decimal
    ymin: Decimal
    ymax: Decimal
```

- `Ausschnitt.aus_text(xmin, xmax, ymin, ymax)` nimmt Zeichenketten an,
  ersetzt ein Komma durch einen Punkt und prüft xmin < xmax und ymin < ymax.
- Gespeichert wird immer `str(Decimal)`. In `float` wird erst unmittelbar
  vor der Rechnung umgewandelt.

Konstanten: `RASTER = 480`, `ABBRUCHGRENZE = 1005`,
`WERT_IN_MENGE = 1006`.

## Algorithmen

### berechnen.py (R1, R2)

```python
def abbruchwerte(ausschnitt, raster=RASTER, grenze=ABBRUCHGRENZE):
    xmin, xmax = float(ausschnitt.xmin), float(ausschnitt.xmax)
    ymin, ymax = float(ausschnitt.ymin), float(ausschnitt.ymax)
    seite_x = (xmax - xmin) / raster
    seite_y = (ymax - ymin) / raster
    nummer = np.arange(1, raster + 1)
    cx = (nummer * seite_x + xmin)[:, None] * np.ones((1, raster))
    cy = np.ones((raster, 1)) * (nummer * seite_y + ymin)[None, :]
    zx = np.zeros((raster, raster))
    zy = np.zeros((raster, raster))
    zaehler = np.zeros((raster, raster), np.int16)
    aktiv = np.ones((raster, raster), bool)
    for _ in range(grenze + 1):
        hx = zx * zx - zy * zy + cx
        hy = 2 * zx * zy + cy
        zx = np.where(aktiv, hx, zx)
        zy = np.where(aktiv, hy, zy)
        zaehler += aktiv
        aktiv &= (zx * zx + zy * zy) < 4
        if not aktiv.any():
            break
    return zaehler
```

Verbindlich sind:

- die Reihenfolge der Rechenschritte in `cx`, `cy`, `hx` und `hy`, genau
  wie in `MANDELDA.PAS`,
- der Zahlentyp `float64` ohne Zusammenfassen von Rechenschritten,
- die Parameter `raster` und `grenze` für die Tests. Die Kommandozeile
  bietet sie nicht an.

Damit liefert die Funktion auf jedem Rechner dieselben Werte. Richtwert
für die Laufzeit: unter 30 Sekunden pro Bild. In der Voranalyse waren es
2,4 Sekunden.

Turbo Pascal rechnete mit dem eigenen 6-Byte-Typ `real`. Das wird nicht
nachgebildet.

### statistik.py (R3)

```python
def haeufigkeit(roh):
    return np.bincount(roh.ravel(), minlength=WERT_IN_MENGE + 1)

def bereichsbreiten(haeufigkeit, schwelle, max_bereiche=255):
    breiten, summe = [0], 0
    for wert in range(1, ABBRUCHGRENZE + 1):
        summe += int(haeufigkeit[wert])
        breiten[-1] += 1
        if summe >= schwelle or wert == ABBRUCHGRENZE:
            breiten.append(0)
            summe = 0
    breiten.pop()
    if len(breiten) > max_bereiche:
        breiten = breiten[:max_bereiche]
        rest = ABBRUCHGRENZE - sum(breiten)
        i = max_bereiche - 1
        while rest > 0:
            anteil = rest if i == 0 else (rest + 1) // 2
            breiten[i] += anteil
            rest -= anteil
            i -= 1
    return breiten

def stufentabelle(breiten):
    tabelle = np.zeros(WERT_IN_MENGE + 1, np.int16)
    wert = 1
    for nummer, breite in enumerate(breiten, start=1):
        tabelle[wert:wert + breite] = nummer
        wert += breite
    return tabelle            # tabelle[0] und tabelle[1006] bleiben 0

def farbstufen(roh, tabelle):
    return tabelle[roh]

def automatische_schwelle(haeufigkeit, max_bereiche=255):
    schwelle = 1
    while len(bereichsbreiten(haeufigkeit, schwelle, 10**6)) > max_bereiche:
        schwelle += 1
    return schwelle
```

Anmerkungen:

- `(rest + 1) // 2` ist das Runden von Turbo Pascal: halbe Werte aufwärts.
- Der Sonderfall `i == 0` kommt mit 255 oder 256 Bereichen nicht vor. Er
  verhindert nur einen Fehler bei sehr kleiner Höchstzahl.
- Mit `schwelle = 0` bekommt jeder Abbruchwert einen eigenen Bereich. Das
  ist der Fall von `M12.DAT`.
- Im Original lief der Zähler bei mehr als 256 Bereichen über das Ende
  eines Feldes hinaus. Die Portierung bildet das Ergebnis nach, nicht den
  Speicherfehler.

### paletten.py (R4)

Die Paletten werden aus denselben Tabellen erzeugt wie in `MANDPAL.PAS`:
eine Folge von Abschnitten mit je einer Schrittweite für Rot, Grün und Blau.

| Nr. | Abschnittslänge | Schrittweiten je Abschnitt (Rot, Grün, Blau) |
| --- | --- | --- |
| 0 | 8 | (0,0,3) (1,1,2) (1,1,3) (1,1,1) (1,1,0) (1,1,0) (1,1,0) (0,0,0) (1,1,0) (0,0,0) (1,1,0), dann 21 mal (0,0,0) |
| 1 | 16 | 3 mal (0,0,1), dann (1,0,1) (1,0,0), 3 mal (1,0,−1), (0,0,−1), 7 mal (0,1,0) |
| 2 | 16 | 3 mal (1,0,0), dann (1,1,0) (0,1,0) (0,2,1) (0,0,1). Danach werden Rot, Grün und Blau auf 0 gesetzt, es folgen 9 mal (0,0,0) |
| 3 | 16 | wie Palette 1 |

Regeln, wie im Original:

1. Rot, Grün und Blau beginnen bei 0. Abschnitt k (ab 0 gezählt) belegt die
   Farben `k · Länge + 1` bis `k · Länge + Länge`.
2. Für jede Farbe wird die Schrittweite addiert. Erreicht ein Wert 64 oder
   mehr, gilt er als gesättigt.
3. Nach jedem Abschnitt wird ein gesättigter Wert auf 64 gesetzt, damit er
   mit negativer Schrittweite wieder sinken kann.
4. Farbe 0 ist Schwarz. Farbe 256 liegt außerhalb der Tabelle und entfällt.
5. Umrechnung auf 8 Bit: gesättigt wird 255, sonst
   `round(wert · 255 / 63)`.

Annahme: Der Wert 255, den das Original bei Sättigung an die Grafikkarte
schickte, bedeutete volle Helligkeit. Die damalige Karte kannte 64 Stufen
je Farbe.

Kontrollwerte in 8 Bit:

| Palette | Farbe 16 | Farbe 64 | Farbe 96 | Farbe 144 | Farbe 255 |
| --- | --- | --- | --- | --- | --- |
| 0 | 32, 32, 162 | 194, 194, 255 | 255, 255, 255 | 255, 255, 255 | 255, 255, 255 |
| 1 und 3 | 0, 0, 65 | 65, 0, 255 | 194, 0, 194 | 255, 0, 0 | 255, 255, 0 |
| 2 | 65, 0, 0 | 255, 65, 0 | 255, 255, 65 | 0, 0, 0 | 0, 0, 0 |

### einfaerben.py (R5)

```python
def bild(stufen, palette):
    index = np.clip(stufen, 0, 255)
    rgb = palette[index]                      # Form (480, 480, 3), [x, y]
    return Image.fromarray(np.ascontiguousarray(rgb.transpose(1, 0, 2)))
```

Durch das Vertauschen der ersten beiden Achsen liegt Spalte 1 links und
Zeile 1 oben.

### original.py (R6)

- Die Datei muss genau 461.760 Bytes groß sein, sonst Fehler.
- Lesen mit `np.fromfile(pfad, dtype="<i2").reshape(481, 480)`. Zeile 0 ist
  die Kopfzeile, die Zeilen 1 bis 480 sind die Farbstufen in der Lage
  `[x − 1, y − 1]`.
- Aus der Kopfzeile werden nur die Felder 1, 3, 5 und 7 gelesen. Der Rest
  der Kopfzeile ist nicht initialisierter Speicher und wird ignoriert.
- Die Lesetabelle ist eine Konstante im Modul, mit dem Dateinamen in
  Großbuchstaben als Schlüssel:

| Datei | Faktor | Koordinaten für die Nachrechnung | Schwelle 1991 |
| --- | --- | --- | --- |
| `M0.DAT` | 1000 | `-2.1`, `0.6`, `-1.35`, `1.35` | 4 |
| `M01.DAT` | 1000 | `-0.3`, `0`, `-0.9`, `-0.6` | 38 |
| `M1.DAT` | 1000 | `-0.429`, `0.201`, `-1.215`, `-0.585` | 14 |
| `M11.DAT` | 1000 | `-0.2175`, `-0.1235`, `-0.7317`, `-0.6378` | 52 |
| `M12.DAT` | 10000 | `-0.1443`, `-0.0504`, `-1.0008`, `-0.9063` | 0 |

- Für eine Datei, die nicht in der Tabelle steht, ist `--faktor` Pflicht.
  Die Koordinaten sind dann Kopfzeilenwert geteilt durch Faktor.
- Die Funktion gibt zurück: Farbstufen, Koordinaten laut Kopfzeile,
  Koordinaten für die Nachrechnung, Faktor.

### vergleich.py (R7)

```python
def vergleiche(original_stufen, roh, schwelle, max_bereiche=256):
    in_menge = roh == WERT_IN_MENGE
    menge = ((original_stufen == 0) == in_menge).mean()
    breiten = bereichsbreiten(haeufigkeit(roh), schwelle, max_bereiche)
    neu = farbstufen(roh, stufentabelle(breiten))
    stufen = (neu == original_stufen).mean()
    return menge, stufen, neu
```

Das Vergleichsbild ist ein PNG mit drei Feldern von je 480 × 480
Bildpunkten nebeneinander, getrennt durch 10 Bildpunkte Abstand: Original,
Neuberechnung, Abweichungen. Im dritten Feld sind übereinstimmende Punkte
dunkelgrau und abweichende weiß.

### ablage.py (R8)

Ein Lauf-Ordner `ausgabe/<Name>/` enthält:

| Datei | Inhalt | Vorhanden bei |
| --- | --- | --- |
| `roh.npy` | Abbruchwerte | berechneten Läufen |
| `stufen.npy` | Farbstufen | allen Läufen |
| `bild.png` | Bild, 480 × 480, RGB | allen Läufen |
| `lauf.json` | Beschreibung | allen Läufen |
| `vergleich.png` | Vergleichsbild | Vergleichen |

`lauf.json`, in UTF-8 mit zwei Leerzeichen Einzug:

```json
{
  "format": 1,
  "programm": "ki-mandelbrot 0.1.0",
  "erzeugt": "2026-11-16T16:50:00+01:00",
  "herkunft": "berechnet",
  "ausschnitt": {"xmin": "-2.1", "xmax": "0.6", "ymin": "-1.35", "ymax": "1.35"},
  "raster": [480, 480],
  "abbruchgrenze": 1005,
  "wert_in_menge": 1006,
  "statistik": {
    "schwelle": 5,
    "schwelle_automatisch": true,
    "max_bereiche": 255,
    "bereiche": 238,
    "breiten": [1, 1, 1]
  },
  "palette": 1
}
```

- `herkunft` ist `berechnet`, `original` oder `neu eingefärbt`.
- Bei `original` kommen `quelldatei`, `faktor` und `ausschnitt_kopfzeile`
  dazu, und `statistik` entfällt.
- Bei `neu eingefärbt` kommt `aus_lauf` mit dem Namen des Ausgangslaufs dazu.
- Bei Vergleichen kommt `vergleich` mit `menge` und `stufen` als Zahlen
  zwischen 0 und 1 dazu.
- `breiten` enthält alle Bereichsbreiten, das Beispiel ist gekürzt.
- Listen von Zahlen stehen in einer Zeile, alles andere ist eingerückt.
- Ein Vergleichslauf hat die Herkunft `berechnet`. In `vergleich` stehen
  neben `menge` und `stufen` auch `grenze_menge`, `grenze_stufen` und
  `bestanden`, dazu kommt `quelldatei`.

Regeln:

- Existiert der Ordner schon, bricht das Programm mit einer Meldung ab.
  Mit `--ueberschreiben` wird er ersetzt.
- Gleiche Eingaben ergeben byte-gleiche `roh.npy` und `stufen.npy` und ein
  bildpunktgleiches `bild.png`. `lauf.json` unterscheidet sich nur in
  `erzeugt`.

## Kommandozeile

Aufruf immer aus dem Ordner des Repos. Koordinaten werden mit
Gleichheitszeichen übergeben, weil negative Zahlen mit Komma sonst als
Option gelesen werden.

```
python -m mandelbrot original Org_Daten/M0.DAT --palette 1
python -m mandelbrot berechne --xmin=-2.1 --xmax=0.6 --ymin=-1.35 --ymax=1.35 --name gesamt
python -m mandelbrot faerbe ausgabe/gesamt --palette 2 --schwelle 20 --name gesamt-rot
python -m mandelbrot vergleiche
python -m mandelbrot vergleiche Org_Daten/M1.DAT
```

| Befehl | Pflicht | Optionen | Ergebnis |
| --- | --- | --- | --- |
| `original DATEI` | Pfad der `.DAT` | `--palette` (0 bis 3, Standard 1), `--faktor`, `--name`, `--ueberschreiben` | Lauf mit Herkunft `original` |
| `berechne` | `--xmin --xmax --ymin --ymax` | `--schwelle` (Zahl oder `auto`, Standard `auto`), `--max-bereiche` (Standard 255), `--palette`, `--name`, `--ueberschreiben` | Lauf mit Herkunft `berechnet` |
| `faerbe LAUF` | Ordner eines Laufs | `--schwelle`, `--max-bereiche`, `--palette`, `--name`, `--ueberschreiben` | neuer Lauf mit Herkunft `neu eingefärbt` |
| `vergleiche [DATEI]` | – | `--schwelle`, `--palette`, `--ueberschreiben` | Tabelle am Bildschirm, je Datei ein Lauf mit `vergleich.png` |

Einzelheiten:

- **Name:** Ohne `--name` heißt der Lauf bei `original` wie die Datei mit
  Palette, zum Beispiel `M0-palette1`. Bei `berechne` und `faerbe` heißt er
  `lauf-JJJJMMTT-HHMMSS`. Bei `vergleiche` heißt er `vergleich-M0`.
- **`faerbe` ohne Optionen:** Schwelle, Höchstzahl und Palette werden vom
  Ausgangslauf übernommen. War dessen Schwelle automatisch, wird sie wieder
  automatisch bestimmt.
- **`faerbe` ohne `roh.npy`:** Bei einem Lauf mit Herkunft `original` gibt es
  keine Abbruchwerte. Dann ist nur `--palette` erlaubt, `--schwelle` führt
  zu einem Fehler.
- **`vergleiche` ohne Datei:** rechnet alle fünf Originale mit den
  Koordinaten und Schwellen der Lesetabelle und mit 256 Bereichen.
- **`vergleiche` mit Datei:** geht nur für Dateien der Lesetabelle.
  `--schwelle` muss hier eine Zahl sein, `auto` ist nicht erlaubt.
- **Namen von Läufen:** Nicht erlaubt sind die Zeichen `/ \ : * ? " < > |`.
- **Ausgabe von `vergleiche`:** je Datei eine Zeile mit Schwelle,
  Mengen-Übereinstimmung, Stufen-Übereinstimmung und dem Urteil nach A2 und
  A3.

Rückgabewerte: 0 bei Erfolg, 1 wenn `vergleiche` eine Grenze aus A2 oder A3
verfehlt, 2 bei falscher Eingabe. Fehlermeldungen sind auf Deutsch und
nennen die falsche Eingabe.

## Tests

Alle Tests laufen mit `python -m pytest`. Richtwert für die Laufzeit:
unter 2 Minuten.

| Test | Prüft | Kriterium |
| --- | --- | --- |
| `test_berechnen` | Punkt mit Betrag ab 2 hat Abbruchwert 1. Der Punkt 0 hat 1006. Zuordnung von Bildpunkt zu Koordinate nach R1, an einem Raster von 4 × 4 von Hand nachgerechnet. Zweimal rechnen ergibt gleiche Felder. | R1, R2 |
| `test_statistik` | Bereichsbreiten an Beispielen von Hand. Summe der Breiten ist immer 1005. Schwelle 0 mit 256 Bereichen ergibt am Ende die Breiten 2, 2, 4, 7, 13, 24, 48, 95, 188, 376. Farbstufen wachsen mit dem Abbruchwert. Automatische Schwelle hält die Höchstzahl ein, und die nächstkleinere Schwelle überschreitet sie. | R3 |
| `test_paletten` | Kontrollwerte der Tabelle oben. Palette 1 gleich Palette 3. Farbe 0 ist Schwarz. | R4 |
| `test_original` | Alle fünf Dateien: Größe, Faktor, Koordinaten laut Kopfzeile, höchste Farbstufe 258, 262, 256, 256, 256. Falsche Dateigröße führt zum Fehler. | R6 |
| `test_ablage` | Schreiben und Lesen eines Laufs. Koordinaten bleiben als Text unverändert, auch mit 30 Nachkommastellen. Vorhandener Ordner führt zum Fehler. | R8, A4 |
| `test_kommandozeile` | Jeder Befehl einmal in einem temporären Ordner. Komma als Dezimalzeichen. `faerbe` rechnet nicht neu. Falsche Eingaben ergeben Rückgabewert 2. | A4, A5 |
| `test_abnahme` | Alle fünf Originale mit allen vier Paletten als PNG. Vergleich aller fünf gegen die Grenzen. | A1, A2, A3 |

Ob `faerbe` neu rechnet, prüft der Test, indem er `abbruchwerte` durch eine
Funktion ersetzt, die einen Fehler auslöst.

### Erwartete Werte in test_abnahme

Gemessen in der Voranalyse am 16.11.2026 mit NumPy und `float64`, gegen
die Dateien in `Org_Daten`, mit den Koordinaten und Schwellen der
Lesetabelle und 256 Bereichen.

| Datei | Menge gemessen | Grenze A2 | Stufen gemessen | Grenze A3 |
| --- | --- | --- | --- | --- |
| `M0.DAT` | 0,9995 | 0,999 | 0,9985 | 0,995 |
| `M01.DAT` | 0,9997 | 0,999 | 0,9923 | 0,990 |
| `M1.DAT` | 0,9998 | 0,999 | 0,9941 | 0,990 |
| `M11.DAT` | 0,9928 | 0,990 | 0,9174 | keine |
| `M12.DAT` | 0,9996 | 0,999 | 0,8608 | keine |

Der Test prüft die Grenzen. Weicht ein gemessener Wert um mehr als 0,0005
von der Tabelle ab, schlägt der Test nicht fehl, gibt aber eine Warnung
aus. Dann ist die Ursache zu klären, bevor abgenommen wird.

Automatische Schwelle mit 255 Bereichen, als weitere Kontrollwerte:

| Datei | Schwelle | Bereiche |
| --- | --- | --- |
| `M0.DAT` | 5 | 238 |
| `M01.DAT` | 39 | 255 |
| `M1.DAT` | 16 | 248 |
| `M11.DAT` | 54 | 253 |
| `M12.DAT` | 1 | 206 |

## Einrichtung

Auf Richards Windows-PC:

```powershell
cd "X:\privat Richard\eigene Programme\Fraktales\KI-Mandel"
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest
```

Auf Thorstens Mac:

```bash
cd ~/KI-Mandelbrot
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest
```

Diese Schritte kommen mit Stufe 1 ins README.

## Zuordnung von Abnahme und Nachweis

| Kriterium | Nachweis |
| --- | --- |
| A1 | `test_abnahme`, dazu die 20 Bilder in `ausgabe/abnahme-a1/`, die der Test dort ablegt |
| A2, A3 | `test_abnahme` und `python -m mandelbrot vergleiche` |
| A4 | `test_ablage`, `test_kommandozeile` |
| A5 | `test_kommandozeile` |
| A6 | Richard öffnet die fünf Dateien `ausgabe/vergleich-*/vergleich.png` |
| A7 | `python -m pytest` |
| A8 | `git tag stufe-1` nach der Abnahme |

## Präzisierungen beim Bauen

Beim Bauen am 16.11.2026 wurde diese Spec an sechs Stellen genauer gefasst.
Die fachliche Spec ist davon nicht berührt.

1. `requirements.txt` enthält zusätzlich `-e .`. Ohne diese Zeile fände
   `python -m mandelbrot` das Paket nicht.
2. `Image.fromarray` wird ohne die Angabe `"RGB"` aufgerufen. Neuere
   Fassungen von Pillow melden diese Angabe als veraltet.
3. `faerbe` übernimmt ohne Optionen die Einstellungen des Ausgangslaufs.
4. `vergleiche` mit Datei ist auf die Lesetabelle beschränkt.
5. `lauf.json` schreibt Zahlenlisten in eine Zeile. Sonst hätte die Datei
   über 250 Zeilen.
6. Die 20 Bilder aus A1 legt der Test unter `ausgabe/abnahme-a1/` ab.

Dazu kommen `.pytest_cache/` und `*.egg-info/` in `.gitignore`.

## Korrektur nach der Abnahme

Richards Abnahmebericht vom 18.11.2026 (`specs/abnahme-stufe-1.md`) nennt
die Auffälligkeit F-01: Die Option `--faktor` überschrieb auch bei den fünf
Dateien der Lesetabelle den Faktor, obwohl die Hilfe sie nur für unbekannte
Dateien vorsieht.

Korrigiert am 18.11.2026: `lies_dat` lehnt einen angegebenen Faktor bei
einer Datei der Lesetabelle mit einer Fehlermeldung ab, auch wenn er mit
dem Faktor der Tabelle übereinstimmt. Der Befehl `original` gibt dann den
Rückgabewert 2 zurück. Nachweis: `tests/test_korrektur_f01.py`.

## Nicht in dieser Stufe

- Numba, CUDA und jede andere Beschleunigung.
- Bildgröße und Abbruchgrenze als Option der Kommandozeile.
- Gebrochene Abbruchwerte.
- Schreiben von `.DAT`-Dateien.
- Automatische Prüfungen bei GitHub.
- Das Format von Job-Dateien. `lauf.json` beschreibt ein Ergebnis, keinen
  Auftrag.

## Offene technische Punkte

| Nr. | Frage | Vorschlag |
| --- | --- | --- |
| T1 | Welche Python-Version ist auf Richards PC installiert? | 3.12 installieren, falls keine oder eine ältere da ist. |
| T2 | Soll `.venv` auf dem Netzlaufwerk liegen? | Ja, zunächst. Wenn es zu langsam ist, auf Laufwerk C: verlegen. |
| T3 | Sollen die 20 Bilder aus A1 ins Repo? | Nein. Sie lassen sich jederzeit neu erzeugen. Ein Übersichtsbild liegt schon in `docs/`. |
