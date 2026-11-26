# Abnahmeprotokoll – Stufe 2a und Stufe 3

## 1. Zusammenfassung

- **Stufe 2a:** Die fachlichen Prüfungen B1–B8 sind laut Spezifikation erfüllt. Die dokumentierten Rechenzeit- und Tiefenbildprüfungen liegen vor. Die Git-Marke `stufe-2a` (B9) ist noch gesondert zu setzen bzw. nachzuweisen.
- **Stufe 3:** Die Ende-zu-Ende-Verarbeitung eines gültigen Jobs sowie die Fehlerbehandlung mit anschließender Verarbeitung eines weiteren Jobs wurden inzwischen händisch geprüft und funktionieren. Weitere Integrations- und Systemprüfungen sowie die Git-Marke `stufe-3` stehen noch aus.
- **Automatisierte Tests:** 547 Tests bestanden.

## 2. Nachweise zu Stufe 2a

### 2.1 Rechenzeiten

Quelle: `docs/abnahme-stufe-2a--rechenzeiten.txt`

| Größe | Auflösung | Rechenzeit |
|---|---:|---:|
| HD | 1280 × 720 | 1,1 s |
| Full HD | 1920 × 1080 | 2,4 s |
| WQHD | 2560 × 1440 | 4,5 s |
| iPad | 2360 × 1640 | 3,6 s |
| 1000 × 700 | 1000 × 700 | 0,5 s |

Messung auf dem Prozessor, ganze Menge, Abbruchgrenze 1005.

### 2.2 Tiefenbild

Quelle: `docs/abnahme-stufe-2a--tiefenbild.txt`

- Mittelpunkt X: `-0.743643887037151`
- Mittelpunkt Y: `0.131825904205330`
- Breite: `0.000000000001`
- Ausgabegröße: WQHD
- Abbruchgrenze: 5000
- PNG-Standardpalette: 1
- Bei der visuellen Prüfung wurden keine Klötzchen festgestellt.

**Einschränkung:** Der Randbereich um die Mandelbrotmenge ist aufgrund der groben Farbzuordnung gelb zugelaufen. Dadurch könnten eventuell vorhandene Klötzchen verdeckt sein. Die Prüfung gilt zunächst als bestanden; nach einer späteren Neuimplementierung der Colorierung ist eine erneute Sichtprüfung erforderlich.

### 2.3 Fachliche Kriterien Stufe 2a

| Kriterium | Status | Hinweis |
|---|---|---|
| B1–B4 | Erfüllt | Laut `specs/stufe-2a-fachlich.md` abgehakt. |
| B5 | Erfüllt mit Vorbehalt | Tiefenbild visuell geprüft; Einschränkung zur Farbzuordnung siehe oben. |
| B6–B8 | Erfüllt | Laut `specs/stufe-2a-fachlich.md` abgehakt. |
| B9 | Offen | Git-Marke `stufe-2a` noch nicht als Abnahmenachweis bestätigt. |

## 3. Automatisierte Tests

Quelle: `docs/abnahme-stufe-2a_und_3-ergebnisse.txt`

- Betriebssystem: Windows (`win32`)
- Python: 3.14.10
- pytest: 9.2.0
- pluggy: 1.7.0
- Tests gesammelt: 547

**Ergebnis: `547 passed in 42.51s`**

Es wurden keine fehlgeschlagenen Tests ausgewiesen.

## 4. Abnahme Stufe 3

### 4.1 Händische Prüfungen

| Prüfung | Ergebnis | Status |
|---|---|---|
| Ende-zu-Ende-Verarbeitung eines gültigen Jobs | Händisch geprüft; funktioniert. | Bestanden |
| Fehlerbehandlung und anschließende Verarbeitung eines weiteren Jobs | Händisch geprüft; funktioniert. | Bestanden |

### 4.2 Weitere Kriterien und offene Prüfungen

| Kriterium | Status | Hinweis |
|---|---|---|
| C1 – Gültiger Job wird vollständig verarbeitet | Bestanden | Ende-zu-Ende händisch geprüft. |
| C2 – Fehler eines Jobs wird behandelt; nachfolgende Jobs laufen weiter | Bestanden | Fehlerfall und Verarbeitung eines weiteren Jobs händisch geprüft. |
| C3 – Verhalten bei Neustart während eines Jobs | Offen | Neustart-/Wiederanlaufprüfung noch dokumentieren. |
| C4 – Job-Server bzw. Verarbeitung über den vorgesehenen Job-Server | Offen | Laut bisherigem README ist der Job-Server noch nicht fertiggestellt. |
| C5 – Verarbeitung über iPad/Browser bzw. vorgesehene Client-Anbindung | Bestanden | Starten und prüfen, sowie Aufrufen der Ergebnisbilder via iPad und Browser händisch geprüft. |
| C6 – Vererbung des Elternbilds bzw. Verhalten bei fehlender Größe | Offen | Fachliche Randfälle noch prüfen. |
| C7 – Ereignisablauf und Ereignisprotokoll | Bestanden |Lauf von fünf Bildern in einer Serie händisch geprüft. |
| C8 – Frühere Tests aus Stufe 1 und 2a bleiben erfolgreich | Bestanden | Gesamtlauf mit 547 bestandenen Tests. |
| C9 – Git-Marke `stufe-3` | Offen | Erst nach Abschluss der noch offenen Prüfungen setzen bzw. nachweisen. |

## 5. Gesamturteil

**Stufe 2a:** Fachlich weitgehend abgenommen. Die dokumentierten Rechenzeit- und Tiefenbildprüfungen sowie die Kriterien B1–B8 liegen vor. B9 (Git-Marke `stufe-2a`) bleibt noch offen. Für B5 ist die dokumentierte Einschränkung der Farbzuordnung zu beachten.

**Stufe 3:** Teilabnahme. Zwei zentrale manuelle Abläufe – erfolgreicher Job und Fehlerfall mit Fortsetzung durch einen weiteren Job – sind nun ausdrücklich geprüft und bestanden. Auch die automatisierte Testsuite ist mit 547 bestandenen Tests grün. Die übrigen Integrations-/Systemprüfungen und die Git-Marke `stufe-3` sind noch offen.

Die Implementierung der nächsten Stufe wird freigegeben. 

## 6. Verwendete Nachweise

- `specs/stufe-2a-fachlich.md`
- `specs/stufe-3-fachlich.md`
- `docs/abnahme-stufe-2a--rechenzeiten.txt`
- `docs/abnahme-stufe-2a--tiefenbild.txt`
- `docs/abnahme-stufe-2a_und_3-ergebnisse.txt`
- `README`
