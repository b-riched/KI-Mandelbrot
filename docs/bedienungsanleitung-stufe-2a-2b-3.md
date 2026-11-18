# Bedienungsanleitung – KI-Mandelbrot, Entwicklungsstufen 2a, 2b und 3

**Version:** 0.2.0  
**Stand:** 18.11.2026  
**Quellstand:** Branch `stufe-3-jobs`  
**Paket:** `ki-mandelbrot`

Diese Anleitung beschreibt die Bedienung des im Branch `stufe-3-jobs` tatsächlich vorhandenen Programmstands. Sie baut auf der [Bedienungsanleitung für Stufe 1](bedienungsanleitung-stufe-1.md) auf. Die Befehle werden in PowerShell bzw. einem Terminal **im Hauptverzeichnis des Repositorys** ausgeführt – nicht im Unterverzeichnis `src/mandelbrot`.

Wichtig zum Umfang dieses Branches: Stufe 2a ist implementiert. Die inhaltliche Spezifikation beschreibt Stufe 2b als GPU-Rechenkern, der in diesem Branch jedoch weder als eigene Spezifikation noch als implementierter CUDA-Rechenkern enthalten ist. Der vorhandene Rechenkern rechnet auf dem Prozessor. Von Stufe 3 ist laut technischer Spec Teil A vorhanden (Einstellungen, Job-Dateien, Warteschlange, Arbeiter, Protokoll und Windows-Autostart). Teil B – Job-Server sowie die Befehle `server` und `start` – steht aus. Diese Funktionen werden deshalb nicht als verfügbar beschrieben.

## 1. Funktionsumfang

| Bereich | Funktion |
| --- | --- |
| Stufe 2a | Bildgröße frei wählen, Ausschnitt durch Mittelpunkt und Bildbreite beschreiben, Abbruchgrenze einstellen, gebrochene Abbruchwerte speichern. |
| Stufe 2b | GPU-Berechnung ist für diesen Branch nicht verfügbar. Die Berechnung erfolgt auf dem Prozessor. |
| Stufe 3 – Teil A | Jobs als JSON-Dateien in einer Warteschlange ablegen und vom Arbeiter nacheinander berechnen lassen. |
| Stufe 3 – Teil A | Jobstatus über Ordner, Fehlertexte und tägliches Ereignisprotokoll nachvollziehen. |
| Stufe 3 – Teil A | Arbeiter beim Anmelden unter Windows über den Autostart-Ordner starten lassen. |

Die vier Befehle aus Stufe 1 – `original`, `berechne`, `faerbe` und `vergleiche` – bleiben erhalten. Hinzu kommen `arbeiter` und `autostart`.

## 2. Voraussetzungen und Installation

- Python **3.12 oder neuer**
- Pakete aus `requirements.txt`: NumPy, Pillow und pytest
- Git-Repository `b-riched/KI-Mandelbrot`, Branch `stufe-3-jobs`
- Für `original` und `vergleiche`: die historischen Dateien im Verzeichnis `Org_Daten/`

### Installation unter Windows

PowerShell öffnen und in das Hauptverzeichnis des Repositorys wechseln:

```powershell
cd "X:\privat Richard\eigene Programme\Fraktales\KI-Mandel"
git switch stufe-3-jobs
```

Virtuelle Umgebung anlegen und Abhängigkeiten installieren:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
```

Falls das Repository noch nicht lokal vorhanden ist:

```powershell
git clone https://github.com/b-riched/KI-Mandelbrot.git
cd KI-Mandelbrot
git switch stufe-3-jobs
```

Unter macOS/Linux:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

In den folgenden Windows-Beispielen wird der Interpreter der virtuellen Umgebung direkt als `.venv\Scripts\python` aufgerufen. Eine Aktivierung der Umgebung ist daher nicht erforderlich.

## 3. Allgemeine Bedienung

Alle Befehle beginnen mit:

```powershell
.venv\Scripts\python -m mandelbrot
```

Version und allgemeine Hilfe:

```powershell
.venv\Scripts\python -m mandelbrot --version
.venv\Scripts\python -m mandelbrot --help
```

Hilfe zu einem einzelnen Befehl:

```powershell
.venv\Scripts\python -m mandelbrot berechne --help
.venv\Scripts\python -m mandelbrot arbeiter --help
.venv\Scripts\python -m mandelbrot autostart --help
```

Die Befehle müssen aus dem Hauptverzeichnis des Repositorys gestartet werden. Dort befinden sich unter anderem `Org_Daten` und – sofern angelegt – die Datei `mandelbrot.toml`. Die Pfade der Ergebnis- und Jobordner beziehen sich standardmäßig auf dieses aktuelle Verzeichnis.

## 4. Bilder mit Stufe 2a berechnen

### 4.1 Ausschnitt und Bildgröße

Neben der historischen Eingabeform mit `xmin`, `xmax`, `ymin` und `ymax` gibt es die neue Form. Sie beschreibt ein Bild durch:

- `--mitte-x`: x-Koordinate des Bildmittelpunkts,
- `--mitte-y`: y-Koordinate des Bildmittelpunkts,
- `--breite`: Breite des Ausschnitts in der Zahlenebene,
- `--groesse`: Bildgröße in Bildpunkten.

Beispiel für die Gesamtansicht in Full HD:

```powershell
.venv\Scripts\python -m mandelbrot berechne --mitte-x=-0.75 --mitte-y=0 --breite=3.5 --groesse fullhd --name gesamt-hd
```

Die Bildmitte liegt bei den angegebenen Mittelpunktkoordinaten. Der Punktabstand ist waagerecht und senkrecht gleich; die Bildpunkte sind quadratisch. Die Bildhöhe des Ausschnitts ergibt sich aus dem Seitenverhältnis. Bilder dieser neuen Form stehen aufrecht: Die y-Koordinate wächst nach oben.

Benannte Bildgrößen:

| Name | Breite × Höhe |
| --- | ---: |
| `hd` | 1280 × 720 |
| `fullhd` | 1920 × 1080 |
| `wqhd` | 2560 × 1440 |
| `ipad` | 2360 × 1640 |

Eine andere Größe wird als `BREITExHÖHE` angegeben, zum Beispiel `800x600`. Jede Seite muss zwischen 16 und 10.000 Bildpunkten liegen. In der neuen Form ist `--groesse` Pflicht.

Beispiel für einen kleineren Ausschnitt:

```powershell
.venv\Scripts\python -m mandelbrot berechne --mitte-x=-0.7436 --mitte-y=0.1318 --breite=0.002 --groesse 800x600 --name ausschnitt
```

### 4.2 Abbruchgrenze

Die Abbruchgrenze legt fest, wie viele Iterationen höchstens ausgeführt werden. Ohne Angabe gilt 1005. Zulässig sind ganze Zahlen von 10 bis 1.000.000.

```powershell
.venv\Scripts\python -m mandelbrot berechne --mitte-x=-0.743643887037151 --mitte-y=0.131825904205330 --breite=0.000000000001 --groesse wqhd --abbruchgrenze 5000 --name tief
```

### 4.3 Statistik und Palette

Die folgenden Optionen gelten für `berechne`:

| Option | Bedeutung |
| --- | --- |
| `--schwelle N` | Ganze Zahl ab 0; steuert die Bildung der Statistikbereiche. |
| `--schwelle auto` | Automatische Wahl der Schwelle; Standard. |
| `--max-bereiche N` | Höchstzahl der Statistikbereiche, 1 bis 256; Standard 255. |
| `--palette N` | Farbpalette 0 bis 3; Standard 1. |
| `--name NAME` | Name des Ergebnisordners unter `ausgabe/`. Ohne Angabe wird ein Zeitname erzeugt. |
| `--ueberschreiben` | Ersetzt einen vorhandenen Ergebnisordner gleichen Namens. |

Beispiel:

```powershell
.venv\Scripts\python -m mandelbrot berechne --mitte-x=-0.75 --mitte-y=0 --breite=3.5 --groesse hd --schwelle 20 --max-bereiche 255 --palette 2 --name gesamt-palette2
```

Die Optionen der neuen Form und die historische Form dürfen nicht gemischt werden. Die historische Form benötigt alle vier Angaben `--xmin`, `--xmax`, `--ymin` und `--ymax`; sie erzeugt weiterhin ein Raster von 480 × 480 Bildpunkten und behält die Bildlage von 1991 bei. Auch in dieser Form kann `--abbruchgrenze` verwendet werden.

### 4.4 Grenze der Rechengenauigkeit

Bei sehr kleinen Bildbreiten kann die Gleitkommarechnung benachbarte Bildpunkte nicht mehr unterscheiden:

- Unterhalb einer Bildbreite von 10⁻¹² wird eine Warnung ausgegeben; die Berechnung läuft trotzdem.
- Liegen benachbarte Spalten oder Zeilen auf derselben berechneten Koordinate, wird die Berechnung mit einem Eingabefehler abgewiesen.
- Eine Warnung ist kein Fehler. Sie wird auf der Fehlerausgabe angezeigt; der Befehl kann trotzdem erfolgreich enden.

Stufe 2a ist nicht für beliebig tiefe Zooms ausgelegt. Die Spezifikation verweist für tiefere Zooms auf eine spätere Stufe 7.

## 5. Ergebnisse aus Stufe 2a

Berechnete Läufe werden weiterhin unter `ausgabe/<Name>/` abgelegt. Je nach Herkunft enthält der Ordner unter anderem:

| Datei | Inhalt |
| --- | --- |
| `bild.png` | Gerendertes PNG-Bild. |
| `lauf.json` | Beschreibung des Laufs einschließlich Koordinaten, Raster, Abbruchgrenze und Statistik. |
| `roh.npy` | Ganze Abbruchwerte. |
| `glatt.npy` | Gebrochene Abbruchwerte für Bilder der neuen Mittelpunkt-/Bildbreitenform. |
| `stufen.npy` | Abgeleitete Farbstufen. |

Die gebrochenen Abbruchwerte werden in Stufe 2a gespeichert, aber noch nicht für die Farbgebung verwendet. Die Einfärbung arbeitet weiterhin mit den ganzen Abbruchwerten.

Ein Lauf aus Stufe 1 im Format 1 bleibt lesbar. Neue Läufe werden im Format 2 beschrieben. Ein Lauf der historischen Form hat kein `glatt.npy`.

## 6. Vorhandene Läufe neu einfärben

Der Befehl `faerbe` bleibt erhalten. Er rechnet die Mandelbrot-Menge nicht erneut, sondern verwendet die gespeicherten Farbstufen bzw. Abbruchwerte.

```powershell
.venv\Scripts\python -m mandelbrot faerbe ausgabe/gesamt-hd --palette 2 --name gesamt-rot
```

Optionen:

| Option | Bedeutung |
| --- | --- |
| `--palette N` | Palette 0 bis 3; ohne Angabe wird die Palette des Ausgangslaufs übernommen. |
| `--schwelle N` oder `auto` | Neue Statistikschwelle, sofern Abbruchwerte vorhanden sind. |
| `--max-bereiche N` | Neue Höchstzahl der Statistikbereiche, 1 bis 256. |
| `--name NAME` | Name des neuen Ergebnisordners. |
| `--ueberschreiben` | Ersetzt einen vorhandenen Ergebnisordner gleichen Namens. |

Der Ausgangslauf bleibt unverändert. Bei einem Lauf aus einer historischen Originaldatei sind keine Abbruchwerte vorhanden; dann kann nur die Palette geändert werden. Die Angabe von `--schwelle` oder `--max-bereiche` führt in diesem Fall zu einem Fehler.

## 7. Stufe 2b – Grafikkarte

Das Stufenkonzept sieht für Stufe 2b vor, den Rechenkern auf der Grafikkarte (vorgesehen: RTX 3080 Ti) mit Numba-CUDA und doppelter Genauigkeit auszuführen. Der Prozessor soll als Ausweichweg erhalten bleiben.

**Dieser GPU-Rechenkern ist im hier dokumentierten Branch `stufe-3-jobs` nicht vorhanden.** Die technische Spezifikation von Stufe 2a nennt Numba/CUDA ausdrücklich als nicht Bestandteil von Stufe 2a. Auch die Stufe-3-Spezifikation behandelt die Grafikkartenrechnung als spätere Austauschbarkeit des Rechenkerns. Es gibt in diesem Branch daher keinen dokumentierten Benutzerparameter zum Auswählen der GPU und keine GPU-Installation, die hier beschrieben werden könnte. Die Befehle aus Abschnitt 4 rechnen auf dem Prozessor.

## 8. Stufe 3 – Jobs und Warteschlange (Teil A)

Ein Job ist ein JSON-Auftrag für eine Bildberechnung. Der Dateiname ohne Endung ist der Jobname. Der Arbeiter nimmt Jobs aus der Warteschlange, rechnet sie nacheinander und legt die Ergebnisse ab.

### 8.1 Ordnerstruktur

Beim Start des Arbeiters werden die benötigten Ordner angelegt, falls sie noch fehlen:

| Ordner | Inhalt |
| --- | --- |
| `_JOBS/neu` | Neue Jobs, die auf die Berechnung warten. |
| `_JOBS/laeuft` | Job, der gerade bearbeitet wird. |
| `_JOBS/fertig` | Erfolgreich bearbeitete Jobs. |
| `_JOBS/fehler` | Gescheiterte Jobs und zugehörige Fehlertexte. |
| `_ERGEBNISSE/<Jobname>/` | Vollständiges Ergebnis des Jobs. |
| `_EVENTS/` | Tägliche Ereignisprotokolle. |

Diese Ordner werden nicht ins Git-Repository eingecheckt. Die Standardnamen und Speicherorte können über `mandelbrot.toml` geändert werden (siehe Abschnitt 10).

### 8.2 Eine Job-Datei anlegen

Lege im Ordner `_JOBS/neu` eine UTF-8-Datei mit der Endung `.json` ab. Der Dateiname wird zum Jobnamen, zum Beispiel `gesamt.json`.

Beispiel für `_JOBS/neu/gesamt.json`:

```json
{
  "mitte_x": "-0.75",
  "mitte_y": "0",
  "breite": "3.5",
  "groesse": "fullhd"
}
```

**Wichtig:** `mitte_x`, `mitte_y` und `breite` müssen Zeichenketten in Anführungszeichen sein. So bleiben die Dezimalstellen erhalten. Eine JSON-Zahl ohne Anführungszeichen wird als Fehler abgewiesen.

Mögliche Angaben:

| Feld | Pflicht | Bedeutung | Standard bzw. Regel |
| --- | --- | --- | --- |
| `mitte_x` | ja | x-Koordinate des Mittelpunkts | Dezimaltext |
| `mitte_y` | ja | y-Koordinate des Mittelpunkts | Dezimaltext |
| `breite` | ja | Bildbreite in der Zahlenebene | Dezimaltext größer 0 |
| `groesse` | bedingt | Bildgröße, z. B. `fullhd` oder `800x600` | Ohne Angabe nur mit vorhandenem Elternbild; dann dessen Rastergröße |
| `abbruchgrenze` | nein | Iterationsgrenze | 1005; zulässig 10 bis 1.000.000 |
| `palette` | nein | Farbpalette | 1; zulässig 0 bis 3 |
| `schwelle` | nein | Statistikschwelle | `"auto"` oder ganze Zahl ab 0 |
| `max_bereiche` | nein | Höchstzahl der Statistikbereiche | 255; zulässig 1 bis 256 |
| `elternbild` | nein | Name eines bereits vorhandenen Ergebnisordners | Das Ergebnis muss existieren |
| `serie` | nein | Freier Name zur Gruppierung zusammengehöriger Jobs | Kein Standard |
| `notiz` | nein | Freier Text | Leer |

Unbekannte Felder sind ein Fehler. Der Jobname wird ausschließlich aus dem Dateinamen abgeleitet; ein Feld `name` gehört nicht in die Job-Datei.

Wenn `groesse` fehlt, muss `elternbild` auf ein bereits vorhandenes Ergebnis verweisen. Die Größe des Elternbildes wird dann übernommen. Fehlen beide Angaben, ist der Job fehlerhaft.

### 8.3 Wann wird ein Job aufgegriffen?

- Der Arbeiter prüft den Ordner `_JOBS/neu` regelmäßig.
- Eine neu angelegte Datei bleibt mindestens zwei Sekunden liegen, damit sie vollständig geschrieben werden kann.
- Danach wird der älteste Job bearbeitet. Maßgeblich ist der Wert `angelegt` in der Job-Datei, falls vorhanden, sonst das Änderungsdatum der Datei.
- Es wird immer nur ein Job gleichzeitig bearbeitet.

### 8.4 Arbeiter starten

Alle wartenden Jobs einmalig abarbeiten und anschließend beenden:

```powershell
.venv\Scripts\python -m mandelbrot arbeiter --einmal
```

Den Arbeiter dauerhaft laufen lassen:

```powershell
.venv\Scripts\python -m mandelbrot arbeiter
```

Der Arbeiter wartet bei leerer Warteschlange standardmäßig zwei Sekunden zwischen den Prüfungen. Beenden mit **Strg+C**. Wird ein laufender Job dabei unterbrochen, bleibt er im Ordner `laeuft`; beim nächsten Start wird er nach `neu` zurückgestellt und vollständig neu gerechnet.

Der Arbeiter prüft die Jobangaben vor der Rechnung. Bei einem Fehler verschiebt er den Job nach `_JOBS/fehler`, legt daneben eine Datei `<Jobname>.fehler.txt` mit einer deutschsprachigen Fehlermeldung ab und fährt mit dem nächsten Job fort. Vorhandene Ergebnisse werden nicht überschrieben.

### 8.5 Ergebnis und Status eines Jobs

Nach erfolgreicher Berechnung:

- liegt der Ergebnisordner unter `_ERGEBNISSE/<Jobname>/`,
- enthält er die Laufdaten und das PNG,
- wird die Jobdatei nach `_JOBS/fertig` verschoben.

Bei einem Fehler liegt die Jobdatei in `_JOBS/fehler`; der Fehlertext steht in der gleichnamigen Datei mit der Endung `.fehler.txt`.

Die Job-Metadaten werden in `lauf.json` im Abschnitt `job` ergänzt. Dort stehen unter anderem Jobname, Elternbild, Serie, Notiz, Anlegezeit, Startzeit, Fertigzeit, Rechenzeit und Warnungen.

## 9. Ereignisprotokoll und Arbeiter-Lebenszeichen

Unter `_EVENTS` wird pro Kalendertag eine Datei `JJJJ-MM-TT.log` angelegt. Jede Zeile enthält, durch Tabulatoren getrennt:

1. Zeitpunkt mit Zeitzone,
2. Jobname oder `-`,
3. Ereignis,
4. kurzen Text.

Protokolliert werden unter anderem Job entdeckt/angelegt, gestartet, fertig, fehlerhaft, nach Neustart zurückgestellt sowie Start und Ende des Arbeiters. Warnungen zur Rechengenauigkeit werden ebenfalls festgehalten.

Zusätzlich schreibt der Arbeiter `_JOBS/arbeiter.json` als Lebenszeichen. Darin stehen Zeitpunkt, aktueller Job (oder `null`) und ob der Arbeiter ordentlich beendet wurde.

## 10. Einstellungen über mandelbrot.toml

Die Einstellungen sind freiwillig. Ohne Datei gelten die eingebauten Standardwerte. Eine Vorlage liegt im Repository als `mandelbrot.beispiel.toml`.

Unter Windows im Hauptverzeichnis des Repositorys:

```powershell
Copy-Item mandelbrot.beispiel.toml mandelbrot.toml
```

Die Vorlage enthält:

```toml
[ordner]
jobs = "_JOBS"
ergebnisse = "_ERGEBNISSE"
ereignisse = "_EVENTS"

[server]
adresse = "0.0.0.0"
port = 8000

[arbeiter]
pause_sekunden = 2
```

Für den derzeit implementierten Teil A sind vor allem die drei Ordnerangaben und `pause_sekunden` relevant. Die Serverwerte sind für den vorgesehenen Job-Server reserviert; ein Job-Server ist in diesem Branch noch nicht enthalten.

Pfade ohne Laufwerksangabe beziehen sich auf das Hauptverzeichnis, aus dem das Programm gestartet wird. Ein Pfad mit Laufwerk wird unverändert verwendet. Unbekannte Abschnitte oder Schlüssel führen zu einer Fehlermeldung.

## 11. Windows-Autostart

Der Autostart legt eine Datei `KI-Mandelbrot.cmd` im Autostart-Ordner des angemeldeten Windows-Benutzers an. Beim Anmelden startet diese Datei den Befehl `python -m mandelbrot start` im Projektverzeichnis.

**Achtung:** Der Befehl `start` und der Job-Server sind im dokumentierten Branch noch nicht implementiert (Teil B steht aus). Der Autostart ist deshalb zwar als Funktion vorhanden, kann den vollständigen Betrieb von Arbeiter und Server in diesem Branch aber noch nicht herstellen. Für den aktuellen Teil A den Arbeiter direkt mit `arbeiter` starten.

Status anzeigen:

```powershell
.venv\Scripts\python -m mandelbrot autostart
```

Autostart einschalten:

```powershell
.venv\Scripts\python -m mandelbrot autostart an
```

Autostart ausschalten:

```powershell
.venv\Scripts\python -m mandelbrot autostart aus
```

Die Funktion steht nur unter Windows zur Verfügung. Die Autostart-Datei wartet, bis das Projektverzeichnis erreichbar ist. Sie startet beim Anmelden des Benutzers, nicht als Windows-Dienst beim Hochfahren des PCs.

## 12. Noch nicht verfügbare Funktionen aus Stufe 3

Die fachliche Spec sieht einen Job-Server vor, über den Jobs aus dem Heimnetz angelegt, Status abgefragt sowie Ergebnislisten, Beschreibungen und Bilder abgerufen werden können. Die technische Spec kennzeichnet diesen Teil jedoch ausdrücklich als Teil B, der noch aussteht.

Im Branch `stufe-3-jobs` fehlen daher derzeit:

- `src/mandelbrot/server.py`,
- die Befehle `server` und `start`,
- die Server-Abhängigkeiten `fastapi`, `uvicorn` und `httpx`,
- die Browser-Testseite des Job-Servers,
- der Zugriff vom iPad bzw. einem anderen Gerät über das Heimnetz.

Es gibt deshalb in diesem Stand noch keine HTTP-Adresse, über die Jobs angelegt oder Ergebnisse abgerufen werden können. Die in der Einstellungsdatei enthaltene Serveradresse und Portnummer allein stellen keinen Server bereit.

## 13. Tests ausführen

Die automatisierten Tests werden aus dem Hauptverzeichnis gestartet:

```powershell
.venv\Scripts\python -m pytest
```

Damit werden die Tests der vorhandenen Stufen ausgeführt. Die technische Spec von Stufe 3 nennt für Teil A unter anderem Tests zu Einstellungen, Jobprüfung, Warteschlange, Protokoll, Arbeiter und Autostart. Die Server-Tests und der vollständige Abnahmetest von Teil B stehen noch aus.

## 14. Fehler und wichtige Hinweise

- **Job wird nicht aufgegriffen:** Prüfen, ob die Datei unter `_JOBS/neu` liegt, auf `.json` endet und mindestens zwei Sekunden unverändert ist.
- **Job landet in `fehler`:** Die Ursache steht in `_JOBS/fehler/<Jobname>.fehler.txt`.
- **Job-Datei wird abgewiesen:** Mittelpunkt und Bildbreite müssen JSON-Zeichenketten sein, also in Anführungszeichen stehen. Unbekannte Felder sind unzulässig.
- **Bildgröße fehlt:** Ohne `groesse` muss ein gültiges, bereits vorhandenes `elternbild` angegeben sein.
- **Ergebnisname bereits vergeben:** Ein Jobname darf weder in einem der vier Jobstatusordner noch als Ergebnisordner vorhanden sein. Ein vorhandenes Ergebnis wird nicht überschrieben.
- **Warnung zur Rechengenauigkeit:** Das Bild wird gerechnet; die Warnung erscheint im Protokoll und in den Laufmetadaten.
- **Autostart auf Nicht-Windows:** Nicht verfügbar.
- **Autostart startet nicht vollständig:** Im vorliegenden Branch fehlt der Befehl `start`; siehe Abschnitt 11.

Eingabefehler werden auf Deutsch ausgegeben. Der Rückgabewert ist 2. Ein erfolgreich ausgeführter Befehl liefert 0.

## 15. Grenzen des dokumentierten Entwicklungsstands

- Stufe 2b (GPU/CUDA) ist in diesem Branch nicht implementiert; gerechnet wird auf dem Prozessor.
- Stufe 3 liegt nur als Teil A vor. Der Job-Server und der gemeinsame Start von Arbeiter und Server fehlen.
- Keine Web-App, Galerie oder grafische Ausschnittwahl; diese gehören zu Stufe 4.
- Keine parallele Bearbeitung durch mehrere Arbeiter.
- Keine Anmeldung und kein Zugriff außerhalb des Heimnetzes.
- Keine Jobs zum nachträglichen Neueinfärben oder für Zoom-Serien.

## 16. Zugehörige Projektdokumente

- [README](../README.md)
- [Stufenkonzept](../specs/stufenkonzept.md)
- [Fachliche Spezifikation Stufe 2a](../specs/stufe-2a-fachlich.md)
- [Technische Spezifikation Stufe 2a](../specs/stufe-2a-technisch.md)
- [Fachliche Spezifikation Stufe 3](../specs/stufe-3-fachlich.md)
- [Technische Spezifikation Stufe 3](../specs/stufe-3-technisch.md)
- [Bedienungsanleitung Stufe 1](bedienungsanleitung-stufe-1.md)
