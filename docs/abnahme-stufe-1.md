# Abnahmebericht – KI-Mandelbrot, Stufe 1

**Ergebnis: Stufe 1 ist abgenommen.**

| Merkmal | Wert |
|---|---|
| Projekt | KI-Mandelbrot |
| Abgenommene Stufe | Stufe 1 – Portierung der Pipeline nach Python |
| Abnahme | Erfolgreich |
| Dokumentationsstand | 18.11.2026 |
| Git-Branch | `stufe-1-portierung` |
| Geprüfter Python-Ausgangsstand | Commit `749e9e274f2c5ce68bff4075d579946d591f50f6` |
| Branch-Stand bei Dokumentation | Commit `f9e0982e6b35730b122d059db59a5058095827a8` |

## 1. Gegenstand und Grundlage

Gegenstand der Abnahme ist die erste Entwicklungsstufe des Projekts KI-Mandelbrot: die Portierung der Berechnungs-, Einfärbungs- und Ablagepipeline nach Python.

Die Prüfung orientierte sich an den Abnahmekriterien A1 bis A8 der Stufe-1-Spezifikation. Der bereitgestellte Python-Quellcode wurde mit dem Quellstand des Stufe-1-Merge-Commits verglichen; die elf Python-Module stimmten nach Normalisierung der Zeilenenden bytegenau mit den entsprechenden Git-Blobs überein.

## 2. Ergebnisse der Abnahmekriterien

| Kriterium | Prüfgegenstand | Ergebnis |
|---|---|---|
| **A1** | Verarbeitung der fünf historischen DAT-Dateien mit jeweils vier Paletten; Erzeugung von insgesamt 20 PNG-Bildern | **Bestanden** |
| **A2** | Vergleich der berechneten Mandelbrot-Mengen mit den historischen Originaldaten | **Bestanden** |
| **A3** | Vergleich der Einfärbungs-/Stufenergebnisse mit den Vorgaben der Spezifikation | **Bestanden** |
| **A4** | Neuberechnung eines ausgewählten Bereichs einschließlich vollständiger Ablage eines Laufs | **Bestanden** – manuell geprüft |
| **A5** | Erneute Einfärbung mit geänderter Palette bzw. Schwelle ohne erneute Berechnung | **Bestanden** – manuell geprüft; die Rohdaten blieben erhalten |
| **A6** | Visuelle Prüfung und fachliche Freigabe durch Richard | **Bestanden** – Freigabe durch Richard bestätigt |
| **A7** | Automatisierte Testsuite, ausführbar mit einem Befehl | **Bestanden** – 119 Tests erfolgreich |
| **A8** | Entwicklungsstand der Stufe 1 im Repository nachvollziehbar hinterlegt | **Bestanden** – Branch `stufe-1-portierung` vorhanden |

### 2.1 Historische Referenzdaten

Für die Prüfung wurden folgende fünf historischen Dateien herangezogen:

- `M0.DAT`
- `M01.DAT`
- `M1.DAT`
- `M11.DAT`
- `M12.DAT`

Für jede Datei wurden vier Paletten verwendet, insgesamt also 20 PNG-Ergebnisse. Die Mengen- und Stufenvergleiche erfüllten die in der Spezifikation festgelegten Abnahmekriterien.

### 2.2 Automatisierte Tests

Die Testsuite wurde mit folgendem Kommando ausgeführt:

```bash
python -m pytest -q
```

**Testergebnis:** 119 bestanden, 0 fehlgeschlagen.  
**Gemessene Laufzeit:** ca. 9,50 Sekunden.

Verwendete Testumgebung:

- Python 3.13.5
- NumPy 2.3.5
- Pillow 12.3.0
- pytest 9.0.2

Zusätzlich wurden Syntax, Import und Kommandozeilen-Hilfe der Python-Module sowie grundlegende Berechnungs-, Statistik-, Paletten-, Ablage- und CLI-Abläufe manuell geprüft.

## 3. Festgestellte technische Auffälligkeit F-01

**Titel:** Überschreibbarkeit des Faktors bei bekannten DAT-Dateien

Die Kommandozeilenhilfe beschreibt die Option `--faktor` als Option „nur für unbekannte Dateien“. In der Funktion `lies_dat(pfad, faktor)` kann der Faktor jedoch auch bei bekannten Dateinamen aus der Lesetabelle überschrieben werden.

Ein synthetischer Prüffall mit `M0.DAT` zeigte, dass ein expliziter Faktor von 2000 die für diese bekannte Datei hinterlegte Skalierung bzw. die daraus abgeleiteten Koordinaten verändert.

**Bewertung:** Dokumentations-/Implementierungsabweichung, die korrigiert werden sollte. Der Befund wurde als separate technische Auffälligkeit festgehalten und verhindert gemäß der im Abnahmeverlauf getroffenen Bewertung nicht die Abnahme der Stufe 1. Eine Korrektur wurde im Rahmen dieser Abnahme nicht vorgenommen.

## 4. Git-Referenz und Ablage

Die Stufe 1 wird im Repository durch den Branch **`stufe-1-portierung`** repräsentiert. Ein Git-Tag `stufe-1` ist hierfür nicht das vereinbarte Ablagekriterium.

Zum Zeitpunkt der Prüfung zeigte der Branch auf:

- Branch: `stufe-1-portierung`
- HEAD: `f9e0982e6b35730b122d059db59a5058095827a8`
- Commit-Nachricht: „Dokumentation: Bedienungsanleitung für Stufe 1“

Der Branch ist damit als Referenz für den abgenommenen Entwicklungsstand dokumentiert.

## 5. Gesamtbewertung und Abnahmeentscheidung

Alle acht Abnahmekriterien A1 bis A8 sind erfüllt. Insbesondere wurde die visuelle Prüfung durch Richard ausdrücklich freigegeben. Die automatisierte Testsuite lief vollständig erfolgreich durch.

**Abnahmeentscheidung: Die Entwicklungsstufe 1 des Projekts KI-Mandelbrot wird als erfolgreich abgenommen bestätigt.**

Der technische Hinweis F-01 bleibt als separater Korrekturpunkt bestehen. Er ist bei der weiteren Entwicklung zu berücksichtigen; im Zuge dieser Abnahme wurden keine Änderungen am Programmcode vorgenommen.

---

*Abnahmeprotokoll auf Grundlage der durchgeführten technischen Prüfungen und der im Projektverlauf bestätigten fachlichen Freigabe.*
