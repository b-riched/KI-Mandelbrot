# Abnahmeprotokoll – Stufe 0: Fundament

**Projekt:** KI-Mandelbrot  
**Repository:** `b-riched/KI-Mandelbrot`  
**Abnahmedatum:** 16.11.2026  
**Ergebnis:** Abgenommen – alle sieben Kriterien erfüllt.

## Beteiligte und Freigaben

- **Thorsten:** Freigabe der Spec am 12.11.2026.
- **Richard:** Übernahme des Pull Requests und Bestätigung der abgeschlossenen
  Abnahme am 16.11.2026.
- **Beiträge:** Beide, Thorsten und Richard, haben Commits in das Repository
  eingebracht.

## Prüfergebnis

| Nr. | Abnahmekriterium | Ergebnis |
|---:|---|---|
| 1 | Ordnerstruktur entspricht der Spec. | Erfüllt |
| 2 | SHA-256-Prüfsummen aller 11 Originaldateien stimmen mit `docs/pruefsummen.txt` und den Originalen auf Richards Laufwerk überein. | Erfüllt |
| 3 | Frische Klone unter Windows und macOS liefern dieselben Prüfsummen. | Erfüllt |
| 4 | Eine `.DAT`-Datei lässt sich anhand der Formatbeschreibung im README ohne Rückgriff auf den Pascal-Quelltext auslesen. | Erfüllt |
| 5 | Thorsten und Richard haben jeweils einen Commit ins Repository eingebracht. | Erfüllt |
| 6 | `LICENSE` ist im Repository vorhanden. | Erfüllt |
| 7 | Der abgenommene Stand ist mit `stufe-0` markiert. | Erfüllt |

## Bestätigung der manuellen Prüfungen

Richard hat bestätigt, dass

1. der Prüfsummenvergleich mit den Originaldateien abgeschlossen ist und
   die Dateien übereinstimmen,
2. frische Klone unter Windows und macOS geprüft wurden und
3. das Einlesen einer `.DAT`-Datei anhand der README-Beschreibung erfolgreich
   getestet wurde.

## Abnahmeentscheidung

Stufe 0 ist fachlich und formal abgenommen. Die in `specs/stufe-0.md`
aufgeführten sieben Abnahmekriterien sind erfüllt. Damit ist das Fundament
für die Arbeiten an Stufe 1 gelegt.

**Hinweis zum Git-Tag:** Dieses Protokoll und die aktualisierte Spec werden
mit einem neuen Commit in `main` aufgenommen. Anschließend sollte der
annotierte Tag `stufe-0` auf diesen Abnahme-Commit gesetzt werden, damit der
Tag den vollständig dokumentierten Abnahmestand bezeichnet.

---

*Protokoll erstellt am 16.11.2026 auf Grundlage der bestätigten Prüfergebnisse
und des Repository-Stands.*
