# Spec Stufe 0: Fundament

Status: freigegeben von Thorsten am 12.11.2026. Richard gibt mit der Übernahme des Pull Requests frei.
Stand: 12.11.2026
Übergeordnet: Stufenkonzept (`specs/stufenkonzept.md`)

## Ziel

Das Repo ist so aufgebaut, dass die Originale von 1990/91 geschützt und
dokumentiert sind und jede spätere Stufe ihren festen Platz hat.

## Ausgangslage

- Das Repo enthält einen Commit mit `Org_Daten/` (5 Dateien) und
  `Org_Sourcen/` (6 Dateien).
- Befund: Die Pascal-Dateien im Repo enthalten keine DOS-Zeilenenden (CR LF)
  mehr. Vermutlich hat Git unter Windows sie beim Einchecken in LF
  umgewandelt. Die Dateien auf Richards Laufwerk sind davon nicht betroffen,
  aber die Fassung im Repo ist dann nicht byte-gleich zum Original.
- Die `.DAT`-Dateien sind unverändert (je 461.760 Bytes).

## Umfang

### 1. Ordnerstruktur

```
KI-Mandelbrot/
├── Org_Daten/          Originaldaten 1991, unverändert
├── Org_Sourcen/        Originalquellen 1990/91, unverändert
├── specs/              Stufenkonzept und eine Spec pro Stufe
├── src/mandelbrot/     Python-Code (ab Stufe 1), vorerst leer
├── tests/              Tests (ab Stufe 1), vorerst leer
├── docs/               Analyse der Originale, Bilder
├── .gitattributes
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

Leere Ordner bekommen eine Datei `.gitkeep`, damit Git sie führt.

### 2. Schutz der Originale

`.gitattributes` mit genau diesem Inhalt:

```
Org_Daten/**    binary
Org_Sourcen/**  -text
```

Danach werden die Pascal-Dateien einmal neu eingecheckt
(`git add --renormalize .`), damit sie mit ihren ursprünglichen Zeilenenden
im Repo liegen.

`docs/pruefsummen.txt` enthält die SHA-256-Prüfsummen aller 11
Originaldateien, erzeugt auf Richards Laufwerk aus den Dateien dort.

### 3. README.md

Gliederung:

1. Was das Projekt ist (drei Sätze, Verweis auf das Stufenkonzept)
2. Die Pipeline von 1991: MANDELDA → MANDELST → MANDELFA mit MANDPAL
3. Was die übrigen Dateien sind (MANDELMO, MANDMAUS)
4. Das `.DAT`-Format (siehe unten)
5. Die fünf Datensätze mit ihren Koordinaten
6. Was fehlt (Units MOUSE und MOUSEWIN, Grafiktreiber, Rohdateien)
7. Stand des Projekts und nächste Stufe

### 4. Beschreibung des .DAT-Formats (Inhalt für README und docs/)

- 481 Datensätze zu je 480 Zahlen, jede Zahl 16 Bit mit Vorzeichen,
  niederwertiges Byte zuerst. Dateigröße 481 × 480 × 2 = 461.760 Bytes.
- Datensatz 1 ist die Kopfzeile. Belegt sind nur vier Felder:
  Feld 1 = xmin, Feld 3 = xmax, Feld 5 = ymin, Feld 7 = ymax,
  jeweils als ganze Zahl = Koordinate × Faktor.
- Faktor: 1000 bei `M0`, `M01`, `M1`, `M11`; 10000 bei `M12`.
  Der Quelltext rechnet mit 10000, er ist also neuer als vier der Dateien.
- Datensätze 2 bis 481 sind die Bildspalten von links nach rechts,
  jede mit 480 Werten von oben nach unten.
- Werte: 0 = Punkt gehört zur Menge, 1 bis etwa 260 = Farbstufe aus
  MANDELST.
- Koordinate eines Punktes (Spalte x, Zeile y, beide ab 1 gezählt):
  cx = xmin + x × (xmax − xmin) / 480, cy = ymin + y × (ymax − ymin) / 480.

### 5. Python-Umgebung

- Python 3.12.
- `requirements.txt` für Stufe 1: `numpy`, `pillow`, `pytest`.
  Numba und CUDA kommen erst mit der Spec für Stufe 2 dazu.
- `.gitignore` für Python (`__pycache__/`, `.venv/`, `*.pyc`) und für
  erzeugte Bilder (`ausgabe/`).

### 6. Lizenz

MIT (entschieden am 12.11.2026). In der Datei `LICENSE` steht als Inhaber
vorerst „b-riched und Mitwirkende". Richard trägt dort seinen Namen ein,
wenn er das möchte.

### 7. Stufenkonzept im Repo

Das Stufenkonzept wird als `specs/stufenkonzept.md` abgelegt. Diese Spec
liegt als `specs/stufe-0.md` daneben.

## Nicht in dieser Stufe

- Kein Python-Code, der rechnet, liest oder Bilder erzeugt.
- Keine Änderung am Inhalt der Originaldateien.
- Keine Umbenennung von `Org_Daten` und `Org_Sourcen`.
- Keine automatischen Prüfungen bei GitHub (CI). Die kommen frühestens mit
  Stufe 1.

## Entscheidungen

| Nr. | Frage | Entscheidung vom 12.11.2026 |
| --- | --- | --- |
| E1 | Lizenz des Repos | MIT |
| E2 | Wer schreibt ins Repo? | Claude baut einen Pull Request, Richard übernimmt ihn. |
| E3 | Commit-Autor | Der erste Commit bleibt, wie er ist. Autor der Commits dieser Stufe ist Thorsten. |

## Arbeitsteilung

Der Pull Request liefert alles aus dem Umfang außer zwei Schritten, die nur
auf Richards Rechner möglich sind, weil dort die unveränderten Originale
liegen:

1. Die Pascal-Dateien neu einchecken (`git add --renormalize .`).
2. `docs/pruefsummen.txt` aus den Dateien auf seinem Laufwerk erzeugen.

## Abnahme

- [ ] Die Ordnerstruktur im Repo entspricht Abschnitt 1.
- [ ] Die Prüfsummen der 11 Originaldateien im Repo stimmen mit
      `docs/pruefsummen.txt` überein (also mit Richards Laufwerk).
- [ ] Ein frischer Klon unter Windows und einer unter macOS liefern
      dieselben Prüfsummen.
- [ ] Jemand liest mit der Formatbeschreibung im README eine `.DAT`-Datei
      aus, ohne in den Pascal-Quelltext zu schauen. (Probe: Claude in einer
      frischen Sitzung nur mit dem README.)
- [ ] Thorsten und Richard haben beide einen Commit ins Repo gebracht.
- [ ] `LICENSE` liegt im Repo.
- [ ] Der Stand trägt die Marke `stufe-0`.

## Ergebnis für die nächste Stufe

Stufe 1 kann sich darauf verlassen, dass die Originale byte-genau im Repo
liegen, das `.DAT`-Format schriftlich festgelegt ist und `src/`, `tests/`
und `requirements.txt` vorhanden sind.
