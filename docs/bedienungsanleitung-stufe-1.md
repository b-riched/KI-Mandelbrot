# Bedienungsanleitung – KI-Mandelbrot, Entwicklungsstufe 1

**Version:** 0.1.0  
**Stand:** 17.11.2026  
**Quellstand:** Branch `stufe-1-portierung`  
**Paket:** `ki-mandelbrot`

Diese Anleitung beschreibt die Bedienung der in Stufe 1 portierten Mandelbrot-Pipeline. Sie orientiert sich am tatsächlich vorhandenen Programmstand. Die Befehle werden in einer PowerShell bzw. einem Terminal **im Hauptverzeichnis des Repositorys** ausgeführt – nicht im Unterverzeichnis `src/mandelbrot`.

## 1. Funktionsumfang

Stufe 1 stellt vier Kommandozeilenbefehle bereit:

| Befehl | Zweck |
| --- | --- |
| `original` | Eine historische `.DAT`-Datei lesen und als PNG ausgeben. |
| `berechne` | Einen frei angegebenen Ausschnitt der Mandelbrot-Ebene neu berechnen. |
| `faerbe` | Einen bereits gespeicherten Lauf erneut einfärben, ohne die Mandelbrot-Rechnung zu wiederholen. |
| `vergleiche` | Historische Originaldaten nachrechnen, Übereinstimmungen bestimmen und Vergleichsbilder erzeugen. |

Die Berechnung erfolgt mit NumPy auf dem Prozessor. Rastergröße (480 × 480) und Abbruchgrenze (1005 Iterationen) sind in Stufe 1 fest vorgegeben und keine Kommandozeilenoptionen.

## 2. Voraussetzungen

- Python **3.12 oder neuer**
- Pakete aus `requirements.txt`: NumPy, Pillow und pytest
- Repository `b-riched/KI-Mandelbrot), Branch `stufe-1-portierung`
- Für die Befehle `original` und `vergleiche` die historischen Dateien im Verzeichnis `Org_Daten/`

## 3. Installation unter Windows

Öffne PowerShell und wechsle in das Hauptverzeichnis des geklonten Repositorys. Beispiel für Richards Rechner:

```powershell
cd "X:\privat Richard\eigene Programme\Fraktales\KI-Mandel"
```

Falls das Repository noch nicht lokal vorhanden ist, kann es mit Git geklont und der Entwicklungsbranch ausgecheckt werden:

```powershell
git clone https://github.com/b-riched/KI-Mandelbrot.git
cd KI-Mandelbrot
git switch stufe-1-portierung
```

Virtuelle Python-Umgebung anlegen und Abhängigkeiten installieren:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
```

Die Zeile `-e .` in `requirements.txt` installiert das Projekt im Entwicklungsmodus. Dadurch ist der Modulaufruf `python -m mandelbrot` möglich.

Unter macOS/Linux lauten die entsprechenden Befehle:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

In den folgenden Windows-Beispielen wird der Interpreter der virtuellen Umgebung direkt als `.venv\Scripts\python` aufgerufen. So ist keine Aktivierung der Umgebung erforderlich.

## 4. Allgemeine Bedienung und Hilfe

Alle Befehle beginnen mit:

```powershell
.venv\Scripts\python -m mandelbrot
```

Versionsnummer anzeigen:

```powershell
.venv\Scripts\python -m mandelbrot --version
```

Allgemeine Hilfe:

```powershell
.venv\Scripts\python -m mandelbrot --help
```

Hilfe zu einem einzelnen Befehl, zum Beispiel:

```powershell
.venv\Scripts\python -m mandelbrot berechne --help
```

Koordinaten sollten mit Gleichheitszeichen angegeben werden, z. B. `--xmin=-2.1`. Das vermeidet insbesondere bei negativen Zahlen Mehrdeutigkeiten bei der Kommandozeilen-Auswertung. Dezimalzahlen dürfen mit Punkt oder Komma geschrieben werden.

## 5. Historisches Originalbild erzeugen – `original`

Mit diesem Befehl wird eine historische `.DAT`-Datei eingelesen und mit einer Farbpalette als PNG gespeichert.

Beispiel:

```powershell
.venv\Scripts\python -m mandelbrot original Org_Daten/M0.DAT --palette 1
```

Parameter:

| Parameter | Bedeutung |
| --- | --- |
| `DATEI` | Pflicht: Pfad zur `.DAT`-Datei. |
| `--palette N` | Palette 0 bis 3; Standard ist 1. |
| `--faktor N` | Koordinatenfaktor der Kopfzeile. Nur erforderlich, wenn die Datei nicht in der eingebauten Lesetabelle enthalten ist. Muss größer als 0 sein. |
| `--name NAME` | Name des Ergebnisordners unter `ausgabe/`. |
| `--ueberschreiben` | Ersetzt einen bereits vorhandenen Ergebnisordner gleichen Namens. |

Die fünf bekannten Originaldateien und ihre Faktoren:

| Datei | Faktor |
| --- | ---: |
| `M0.DAT` | 1000 |
| `M01.DAT` | 1000 |
| `M1.DAT` | 1000 |
| `M11.DAT` | 1000 |
| `M12.DAT` | 10000 |

Für diese fünf Dateien wird der Faktor automatisch aus der Lesetabelle übernommen. Bei anderen Dateien im gleichen Dateiformat muss `--faktor` angegeben werden. Die Datei muss exakt 461.760 Bytes groß sein.

Beispiel mit eigenem Namen und Palette 2:

```powershell
.venv\Scripts\python -m mandelbrot original Org_Daten/M12.DAT --palette 2 --name M12-gelb
```

Ein Original-Lauf enthält keine Abbruchwerte (`roh.npy`). Deshalb kann ein solcher Lauf später nur mit einer anderen Palette, nicht aber mit einer anderen Schwelle neu eingefärbt werden.

## 6. Eigenen Ausschnitt berechnen – `berechne`

Der Befehl berechnet die Abbruchwerte für ein Rechteck der komplexen Zahlenebene und leitet daraus Farbstufen und ein PNG-Bild ab.

Beispiel für die Gesamtansicht:

```powershell
.venv\Scripts\python -m mandelbrot berechne --xmin=-2.1 --xmax=0.6 --ymin=-1.35 --ymax=1.35 --name gesamt
```

Pflichtparameter:

| Parameter | Bedeutung |
| --- | --- |
| `--xmin` | Linke Grenze des Ausschnitts. |
| `--xmax` | Rechte Grenze des Ausschnitts. |
| `--ymin` | Obere Grenze des Ausschnitts. |
| `--ymax` | Untere Grenze des Ausschnitts. |

Es muss gelten: `xmin < xmax` und `ymin < ymax`.

Optionale Parameter:

| Parameter | Bedeutung |
| --- | --- |
| `--schwelle N` | Ganze Zahl ab 0; legt fest, ab wie vielen Bildpunkten ein Statistikbereich geschlossen wird. Standard: `auto`. |
| `--schwelle auto` | Ermittelt automatisch die kleinste Schwelle, bei der höchstens die vorgegebene Zahl von Bereichen entsteht. Dies ist die Standardeinstellung. |
| `--max-bereiche N` | Höchstzahl der Statistikbereiche, zulässig 1 bis 256. Standard: 255. |
| `--palette N` | Palette 0 bis 3. Standard: 1. |
| `--name NAME` | Name des Ergebnisordners. Ohne Angabe wird ein Zeitname `lauf-JJJJMMTT-HHMMSS` erzeugt. |
| `--ueberschreiben` | Ersetzt einen vorhandenen Ergebnisordner gleichen Namens. |

Beispiel mit expliziter Schwelle und Palette:

```powershell
.venv\Scripts\python -m mandelbrot berechne --xmin=-2.1 --xmax=0.6 --ymin=-1.35 --ymax=1.35 --schwelle 20 --max-bereiche 255 --palette 2 --name gesamt-palette2
```

Koordinaten werden als Dezimaltext in `lauf.json` gespeichert. Die Eingabegenauigkeit bleibt dort erhalten; erst für die numerische Berechnung werden die Werte in Gleitkommazahlen umgewandelt.

## 7. Einen vorhandenen Lauf neu einfärben – `faerbe`

Mit `faerbe` wird ein zuvor erzeugter Lauf eingelesen und als neuer Lauf mit einer anderen Farbgebung gespeichert. Wenn Abbruchwerte vorhanden sind, können auch Statistikschwelle und Höchstzahl der Bereiche geändert werden. Die Mandelbrot-Iteration wird dabei nicht erneut ausgeführt.

Beispiel:

```powershell
.venv\Scripts\python -m mandelbrot faerbe ausgabe/gesamt --palette 2 --name gesamt-rot
```

Parameter:

| Parameter | Bedeutung |
| --- | --- |
| `LAUF` | Pflicht: Ordner eines vorhandenen Laufs, z. B. `ausgabe/gesamt`. |
| `--palette N` | Neue Palette 0 bis 3. Ohne Angabe wird die Palette des Ausgangslaufs übernommen. |
| `--schwelle N` oder `auto` | Neue Statistikschwelle. Ohne Angabe wird die Einstellung des Ausgangslaufs übernommen bzw. bei ursprünglich automatischer Schwelle erneut automatisch bestimmt. |
| `--max-bereiche N` | Neue Höchstzahl der Bereiche, 1 bis 256. Ohne Angabe wird der Wert des Ausgangslaufs übernommen. |
| `--name NAME` | Name des neuen Ergebnisordners. Ohne Angabe wird ein Zeitname erzeugt. |
| `--ueberschreiben` | Ersetzt einen vorhandenen Ergebnisordner gleichen Namens. |

**Wichtig:** Stammt der Ausgangslauf aus dem Befehl `original`, sind keine Abbruchwerte vorhanden. In diesem Fall ist nur das Ändern der Palette möglich. Die Angabe von `--schwelle` oder `--max-bereiche` führt zu einer Fehlermeldung.

Der Ausgangslauf wird nicht verändert. Das Ergebnis wird immer in einem eigenen Laufordner abgelegt.

## 8. Originale nachrechnen und vergleichen – `vergleiche`

Ohne Dateiangabe werden alle fünf historischen Originale nachgerechnet:

```powershell
.venv\Scripts\python -m mandelbrot vergleiche
```

Es kann auch eine einzelne Datei angegeben werden:

```powershell
.venv\Scripts\python -m mandelbrot vergleiche Org_Daten/M1.DAT
```

Optionen:

| Parameter | Bedeutung |
| --- | --- |
| `DATEI` | Optional: eine der fünf Dateien aus der eingebauten Lesetabelle. Ohne Angabe werden alle fünf Dateien bearbeitet. |
| `--schwelle N` | Optionale numerische Schwelle. Ohne Angabe wird die für das jeweilige Original dokumentierte Schwelle von 1991 verwendet. `auto` ist bei diesem Befehl nicht zulässig. |
| `--palette N` | Palette 0 bis 3 für die erzeugten Bilder; Standard ist 1. |
| `--ueberschreiben` | Ersetzt vorhandene Vergleichsläufe gleichen Namens. |

Für den Vergleich werden die Koordinaten und Standardschwellen aus der eingebauten Lesetabelle verwendet. Der Vergleich berechnet zwei Kennzahlen:

- **Mengen-Übereinstimmung:** Anteil der Bildpunkte, bei denen Original und Neuberechnung dieselbe Aussage zur Zugehörigkeit zur Mandelbrot-Menge treffen.
- **Stufen-Übereinstimmung:** Anteil der Bildpunkte, deren Farbstufe exakt übereinstimmt.

Die Tabelle im Terminal zeigt je Datei Schwelle, gemessene Übereinstimmungen, Abnahmegrenzen und Urteil. Zusätzlich wird je Datei ein Laufordner `ausgabe/vergleich-<Dateiname>/` erzeugt. Darin befindet sich `vergleich.png` mit drei nebeneinanderliegenden Feldern: Original, Neuberechnung und Abweichungsdarstellung. Im rechten Feld sind gleiche Bildpunkte dunkelgrau und abweichende weiß.

Die Abnahmegrenzen sind in der fachlichen Spezifikation festgelegt. Für M11 und M12 wird die Stufen-Übereinstimmung ausgewiesen, aber keine Mindestgrenze verlangt.

## 9. Ergebnisdateien und Ablage

Alle Ergebnisse werden relativ zum aktuellen Arbeitsverzeichnis unter `ausgabe/` gespeichert. Deshalb ist es wichtig, die Befehle aus dem Hauptverzeichnis des Repositorys zu starten.

Ein Laufordner enthält – abhängig vom Befehl – folgende Dateien:

| Datei | Inhalt |
| --- | --- |
| `roh.npy` | Abbruchwerte der Berechnung; bei berechneten Läufen und Vergleichsläufen vorhanden. |
| `stufen.npy` | Farbstufen; bei allen Läufen vorhanden. |
| `bild.png` | Gerendertes RGB-Bild mit 480 × 480 Bildpunkten. |
| `lauf.json` | Metadaten zum Lauf, z. B. Ausschnitt, Palette, Herkunft und Statistikparameter. |
| `vergleich.png` | Vergleichsbild; nur bei Vergleichsläufen vorhanden. |

Die Datei `lauf.json` enthält unter anderem:

- Programmversion und Erzeugungszeitpunkt,
- Herkunft (`original`, `berechnet` oder `neu eingefärbt`),
- Koordinaten des Ausschnitts,
- Rastergröße, Abbruchgrenze und Wert für Punkte in der Menge,
- verwendete Palette,
- bei berechneten Läufen die Schwelle, Höchstzahl und Breiten der Statistikbereiche,
- bei Original-Läufen Quelldatei und Faktor,
- bei neu eingefärbten Läufen den Namen des Ausgangslaufs,
- bei Vergleichsläufen die Vergleichswerte und das Urteil.

Die Ausgabe wird nicht automatisch ins Git-Repository eingecheckt. Der Ordner `ausgabe/` ist als lokale Ergebnisablage vorgesehen.

## 10. Farbpaletten

Es stehen vier aus dem Original übernommene Paletten zur Verfügung:

| Nummer | Farbverlauf |
| ---: | --- |
| 0 | Schwarz über Blau und Hellblau nach Weiß; ab Farbe 88 Weiß. |
| 1 | Schwarz über Blau, Violett und Rot nach Gelb; ab Farbe 208 Gelb. |
| 2 | Schwarz über Rot und Gelb nach Hellgelb; ab Farbe 113 Schwarz. |
| 3 | Identisch mit Palette 1. |

Palette 1 ist die Standardeinstellung. Farbstufen über 255, die in historischen Originaldateien vorkommen können, werden mit Palettenfarbe 255 dargestellt.

## 11. Verhalten bei Fehlern und Überschreiben

- Ein vorhandener Laufordner wird **nicht stillschweigend überschrieben**.
- Soll ein vorhandener Lauf ersetzt werden, muss ausdrücklich `--ueberschreiben` angegeben werden.
- Alternativ kann mit `--name` ein anderer Laufname gewählt werden.
- In Laufnamen sind folgende Zeichen nicht erlaubt: `/ \ : * ? " < > |`.
- Eine `.DAT`-Datei mit falscher Dateigröße wird zurückgewiesen.
- Für unbekannte `.DAT`-Dateien ist `--faktor` erforderlich.
- Falsche oder fehlende Eingaben werden mit einer deutschsprachigen Fehlermeldung ausgegeben.

Rückgabewerte des Programms:

| Rückgabewert | Bedeutung |
| ---: | --- |
| 0 | Befehl erfolgreich. |
| 1 | Der Vergleichsbefehl hat mindestens eine festgelegte Abnahmegrenze verfehlt. |
| 2 | Eingabefehler bzw. ungültige Kommandozeilenangabe. |

**Achtung bei `--ueberschreiben`:** Der bestehende Ergebnisordner wird vollständig gelöscht und neu angelegt. Darin enthaltene Dateien gehen verloren.

## 12. Tests ausführen

Die automatisierten Tests werden aus dem Hauptverzeichnis des Repositorys gestartet:

```powershell
.venv\Scripts\python -m pytest
```

Der Testlauf prüft unter anderem Berechnung, Statistik, Paletten, Lesen der Originaldateien, Ablage, Kommandozeilenbedienung und Abnahmekriterien A1 bis A3.

Für die manuelle Prüfung der fünf Vergleichsbilder:

1. `python -m mandelbrot vergleiche` ausführen.
2. Die fünf erzeugten Ordner unter `ausgabe/vergleich-*/` öffnen.
3. In jedem Ordner `vergleich.png` betrachten.
4. Die Bilder fachlich beurteilen und die Ergebnisse für A6 dokumentieren.

## 13. Grenzen von Entwicklungsstufe 1

Nicht Bestandteil dieser Stufe sind unter anderem:

- frei wählbare Bildgröße oder Abbruchgrenze,
- GPU-/CUDA-Beschleunigung oder parallele Berechnung,
- grafische Bedienoberfläche und Ausschnittwahl mit der Maus,
- neue Farbverläufe oder erweiterte Fraktaldarstellungen,
- Schreiben historischer `.DAT`-Dateien,
- Zoom-Videos, Jobs, Server oder Web-App.

Die Bildlage entspricht dem historischen Programm: Spalte 1 liegt links, Zeile 1 oben; die y-Koordinate wächst im Bild nach unten. Die PNG-Bilder haben keine Achsen oder Beschriftungen. Einzelne Randpunkte können aufgrund des anderen Zahlenformats gegenüber Turbo Pascal abweichen.

## 14. Zugehörige Projektdokumente

- [README](../README.md)
- [Fachliche Spezifikation Stufe 1](../specs/stufe-1-fachlich.md)
- [Technische Spezifikation Stufe 1](../specs/stufe-1-technisch.md)
- [Stufenkonzept](../specs/stufenkonzept.md)
