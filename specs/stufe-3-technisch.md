# Stufe 3: Jobs und Server – technische Spec

Status: freigegeben von Thorsten am 16.11.2026. Richard gibt mit der Übernahme des Pull Requests frei.
Stand: 16.11.2026. Teil A ist gebaut, Teil B steht aus, siehe „Stand des Baus"
Übergeordnet: [Stufenkonzept](stufenkonzept.md)
Gegenstück: [fachliche Spec](stufe-3-fachlich.md)
Baut auf: [technische Spec Stufe 2a](stufe-2a-technisch.md)

Die Regeln R17 bis R26 und die Abnahmekriterien C1 bis C9 stehen in der
fachlichen Spec.

## Rahmen

| Thema | Festlegung |
| --- | --- |
| Neue Abhängigkeiten | `fastapi`, `uvicorn` für den Job-Server, `httpx` für dessen Tests |
| Einstellungen | Datei `mandelbrot.toml` im Projektordner, gelesen mit `tomllib` aus der Standardbibliothek |
| Prozesse | Arbeiter und Job-Server sind zwei getrennte Prozesse. Sie teilen sich nur die Ordner. |
| Rechnen | `berechnen.berechne_bild` aus Stufe 2a, unverändert |

Leitlinie wie in Stufe 2a: Kein Test aus den Stufen 1 und 2a wird
geändert.

Der Arbeiter und alles, was er braucht, kommen ohne die neuen
Abhängigkeiten aus. Nur `server.py` importiert `fastapi`.

## Neue und geänderte Dateien

| Datei | Inhalt |
| --- | --- |
| `src/mandelbrot/einstellungen.py` | neu: Einstellungen lesen, Ordner anlegen |
| `src/mandelbrot/jobs.py` | neu: Job prüfen, lesen, schreiben (R18, R19) |
| `src/mandelbrot/warteschlange.py` | neu: Ordner der Warteschlange, Reihenfolge, Verschieben (R17, R20, R23) |
| `src/mandelbrot/protokoll.py` | neu: Protokoll schreiben (R25) |
| `src/mandelbrot/arbeiter.py` | neu: Jobs abarbeiten (R21, R22, R23) |
| `src/mandelbrot/server.py` | neu: Job-Server (R24) |
| `src/mandelbrot/autostart.py` | neu: Autostart unter Windows (R26) |
| `src/mandelbrot/kommandozeile.py` | neue Befehle `arbeiter`, `server`, `start`, `autostart` |
| `requirements.txt` | `fastapi`, `uvicorn`, `httpx` |
| `.gitignore` | `_JOBS/`, `_EVENTS/`, `_ERGEBNISSE/`, `mandelbrot.toml` |
| `mandelbrot.beispiel.toml` | neu: Vorlage für die Einstellungen |
| `tests/test_jobs.py`, `test_warteschlange.py`, `test_protokoll.py`, `test_arbeiter.py`, `test_server.py`, `test_autostart.py`, `test_abnahme_3.py` | neu |

## Einstellungen

`mandelbrot.toml` ist freiwillig. Ohne die Datei gelten diese Werte:

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

- Pfade ohne Laufwerk gelten ab dem Ordner, in dem das Programm gestartet
  wird. Das ist der Projektordner.
- Ein unbekannter Abschnitt oder Schlüssel ist ein Fehler.
- `einstellungen.lade(ordner=Path.cwd())` gibt ein unveränderliches Objekt
  zurück. Alle anderen Module bekommen es als Parameter. Kein Modul liest
  die Datei selbst.

## Job-Datei (R18, R19)

```json
{
  "mitte_x": "-0.743643887037151",
  "mitte_y": "0.131825904205330",
  "breite": "0.00001",
  "groesse": "fullhd",
  "abbruchgrenze": 5000,
  "palette": 1,
  "elternbild": "gesamt",
  "serie": "seepferdchen"
}
```

- Kodierung UTF-8. Zahlen für Mittelpunkt und Bildbreite stehen als
  Zeichenketten in der Datei, damit keine Stelle verloren geht. Steht dort
  eine JSON-Zahl, ist das ein Fehler mit dem Hinweis auf die
  Anführungszeichen.
- Der Job-Server ergänzt beim Anlegen `angelegt` mit dem Zeitpunkt. Bei
  einer von Hand abgelegten Datei gilt ihr Änderungsdatum.
- `jobs.pruefe(angaben, name, ergebnisse)` wendet R18 und R19 an und gibt
  einen geprüften Job zurück: `Bildausschnitt`, Abbruchgrenze, Palette,
  Schwelle, Höchstzahl, Elternbild, Serie, Notiz. Fehler sind
  `Eingabefehler` mit deutschem Text. Arbeiter und Job-Server benutzen
  dieselbe Funktion.
- Geprüft wird dabei auch: Der Jobname ist als Ordnername erlaubt
  (`ablage.pruefe_name`). Das Elternbild existiert als Ergebnis. Die
  Genauigkeit reicht nach R15.

## Warteschlange (R17, R20, R23)

- Ein Job wechselt den Stand durch Umbenennen der Datei in den
  Nachbarordner (`os.replace`). Auf demselben Laufwerk ist das ein
  einziger Schritt.
- `warteschlange.naechster()` liefert den ältesten Job aus `neu`. Sortiert
  wird nach `angelegt`, ersatzweise nach dem Änderungsdatum der Datei, bei
  Gleichstand nach dem Namen. Dateien, die jünger als zwei Sekunden sind,
  und Dateien, die nicht auf `.json` enden, bleiben liegen.
- Der Job-Server schreibt einen neuen Job zuerst als `<Jobname>.json.teil`
  und benennt ihn dann um. Der Arbeiter sieht so nie eine halbe Datei.
- `warteschlange.raeume_auf()` läuft beim Start des Arbeiters: Jobs aus
  `laeuft` wandern zurück nach `neu`. Ordner `<Jobname>.teil` in
  `_ERGEBNISSE` werden gelöscht.
- Ein Jobname ist vergeben, wenn es in einem der vier Ordner eine Datei
  `<Jobname>.json` gibt oder in `_ERGEBNISSE` einen Ordner dieses Namens.

## Arbeiter (R21, R22)

```python
def arbeite(einstellungen, einmal=False, soll_enden=lambda: False):
    warteschlange.raeume_auf(einstellungen)
    protokoll.schreibe(einstellungen, "-", "arbeiter gestartet")
    while not soll_enden():
        job = warteschlange.naechster(einstellungen)
        if job is None:
            if einmal:
                break
            schreibe_lebenszeichen(einstellungen, None)
            time.sleep(einstellungen.pause_sekunden)
            continue
        bearbeite(einstellungen, job)
    protokoll.schreibe(einstellungen, "-", "arbeiter beendet")
```

`bearbeite` für einen Job:

1. Datei nach `laeuft` verschieben, Lebenszeichen mit dem Jobnamen
   schreiben, Ereignis `gestartet`.
2. Datei lesen und mit `jobs.pruefe` prüfen.
3. `berechne_bild`, Statistik und Einfärben wie beim Befehl `berechne`.
4. Ergebnis mit `ablage.schreibe_lauf` nach `_ERGEBNISSE/<Jobname>.teil`
   schreiben, dann den Ordner in `<Jobname>` umbenennen.
5. Datei nach `fertig` verschieben, Ereignis `fertig` mit Rechenzeit.

Bei einem `Eingabefehler` oder jeder anderen Ausnahme in den Schritten 2
bis 5: Datei nach `fehler` verschieben, `<Jobname>.fehler.txt` daneben
schreiben, Ereignis `fehler`. Bei einer unerwarteten Ausnahme enthält die
Textdatei zusätzlich die Fehlerspur. Der Arbeiter läuft weiter.

`lauf.json` bekommt einen Abschnitt `job`:

```json
"job": {
  "name": "seepferdchen-01",
  "elternbild": "gesamt",
  "serie": "seepferdchen",
  "notiz": "",
  "angelegt": "2026-11-16T22:20:00+01:00",
  "gestartet": "2026-11-16T22:20:03+01:00",
  "fertig": "2026-11-16T22:20:09+01:00",
  "rechenzeit_sekunden": 5.8,
  "warnungen": []
}
```

Das Format von `lauf.json` bleibt 2. Der Abschnitt `job` kommt nur dazu.

**Lebenszeichen:** Der Arbeiter schreibt `_JOBS/arbeiter.json` mit
Zeitpunkt und dem Namen des laufenden Jobs oder `null`. Der Job-Server
meldet den Arbeiter als aktiv, wenn dort ein Job eingetragen ist oder der
Zeitpunkt höchstens 30 Sekunden zurückliegt.

## Protokoll (R25)

- Datei `_EVENTS/JJJJ-MM-TT.log`, UTF-8, Zeilen werden angehängt.
- Eine Zeile hat vier Felder, getrennt durch Tabulatoren: Zeitpunkt mit
  Zeitzone, Jobname oder `-`, Ereignis, Text. Zeilenumbrüche im Text
  werden durch Leerzeichen ersetzt.
- Ereignisse: `angelegt`, `entdeckt`, `gestartet`, `fertig`, `fehler`,
  `zurueckgestellt`, `warnung`, `arbeiter gestartet`, `arbeiter beendet`,
  `server gestartet`, `server beendet`.
- `entdeckt` schreibt der Arbeiter, wenn er einen Job ohne `angelegt`
  aufnimmt.

## Job-Server (R24)

FastAPI, gestartet mit `uvicorn`. Alle Antworten sind JSON, außer dem Bild.

| Aufruf | Zweck | Antwort |
| --- | --- | --- |
| `GET /api/zustand` | Zustand | Programmversion, Zahl der Jobs je Stand, Zahl der Ergebnisse, `arbeiter_aktiv`, laufender Job |
| `POST /api/jobs` | Job anlegen | 201 mit dem Job. 400 mit `{"fehler": "..."}` bei falschen Angaben. 409, wenn der Name vergeben ist. |
| `GET /api/jobs` | alle Jobs, neueste zuerst. Mit `?stand=neu` gefiltert. | Liste |
| `GET /api/jobs/{name}` | ein Job mit Stand, Angaben und bei Fehlern dem Grund | Job oder 404 |
| `GET /api/ergebnisse` | alle Ergebnisse, neueste zuerst | Liste mit Name, Bildgröße, Elternbild, Serie, Zeitpunkt, Adresse des Bildes |
| `GET /api/ergebnisse/{name}` | Beschreibung eines Ergebnisses | Inhalt von `lauf.json` oder 404 |
| `GET /api/ergebnisse/{name}/bild.png` | das Bild | PNG oder 404 |
| `GET /` | Weiterleitung auf die Testseite `/docs` | – |

Einzelheiten:

- `POST /api/jobs` nimmt die Angaben aus R18 als JSON an, dazu freiwillig
  `name`. Ohne Namen heißt der Job `job-JJJJMMTT-HHMMSS`, bei Gleichstand
  mit angehängter Zahl.
- Die Angaben werden als einfaches Wörterbuch angenommen und mit
  `jobs.pruefe` geprüft. So kommen alle Fehlermeldungen auf Deutsch und
  aus derselben Quelle wie beim Arbeiter.
- Namen in Adressen werden mit `ablage.pruefe_name` geprüft, bevor daraus
  ein Pfad wird.
- Der Job-Server schreibt nur in `_JOBS/neu` und ins Protokoll. Alles
  andere liest er nur.
- `server.erzeuge_app(einstellungen)` gibt die Anwendung zurück. Die Tests
  benutzen sie mit dem Testwerkzeug von FastAPI, ohne einen Port zu öffnen.

## Kommandozeile (R26)

```
python -m mandelbrot start
python -m mandelbrot arbeiter
python -m mandelbrot arbeiter --einmal
python -m mandelbrot server
python -m mandelbrot autostart
python -m mandelbrot autostart an
python -m mandelbrot autostart aus
```

| Befehl | Wirkung |
| --- | --- |
| `start` | startet den Arbeiter als eigenen Prozess und danach den Job-Server. Mit Strg+C enden beide. |
| `arbeiter` | arbeitet die Warteschlange ab, bis Strg+C gedrückt wird. Ein laufender Job wird dabei abgebrochen und beim nächsten Start neu gerechnet. |
| `arbeiter --einmal` | arbeitet alle wartenden Jobs ab und endet dann |
| `server` | startet nur den Job-Server und gibt die Adressen aus, unter denen er im Heimnetz erreichbar ist |
| `autostart` | zeigt, ob der Autostart an ist |
| `autostart an`, `autostart aus` | schaltet ihn |

**Autostart:** `autostart an` schreibt die Datei `KI-Mandelbrot.cmd` in
den Autostart-Ordner des angemeldeten Benutzers
(`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`). Sie wechselt
in den Projektordner und ruft `start` mit dem Python auf, mit dem der
Befehl gegeben wurde. `autostart aus` löscht die Datei. Auf anderen
Betriebssystemen meldet der Befehl, dass es den Autostart nur unter
Windows gibt.

## Tests

| Test | Prüft | Kriterium |
| --- | --- | --- |
| `test_jobs` | jede Angabe aus R18 mit gültigen und ungültigen Werten, unbekannte Felder, Zahl statt Zeichenkette, R19 in allen drei Fällen, fehlendes Elternbild | R18, R19, C5 |
| `test_warteschlange` | Reihenfolge nach `angelegt` und Änderungsdatum, junge Dateien bleiben liegen, Verschieben, Aufräumen nach Neustart, vergebene Namen | R17, R20, R23 |
| `test_protokoll` | Zeilenformat, eine Datei pro Tag, Zeilenumbrüche im Text | R25 |
| `test_arbeiter` | ein Job von der Datei bis zum Ergebnis. Fehlerhafter Job mit Meldung, danach läuft der nächste. Vorhandenes Ergebnis wird nicht überschrieben. Abbruch mitten im Job und Neustart. Abschnitt `job` in `lauf.json`. | R21, R22, R23, C1, C2, C3, C6 |
| `test_server` | jeder Aufruf der Tabelle mit Erfolg und Fehler, Namen mit Pfadzeichen, Zustand mit und ohne Lebenszeichen | R24, C4, C5 |
| `test_autostart` | Datei wird geschrieben und gelöscht, Inhalt nennt Projektordner und Python, Meldung auf anderen Betriebssystemen | R26 |
| `test_abnahme_3` | drei Jobs über den Job-Server anlegen, davon einer fehlerhaft und einer mit Elternbild, dann `arbeiter --einmal`, dann Stand, Ergebnisse, Bild und Protokoll prüfen | C1, C2, C5, C6 |

- Alle Tests arbeiten in temporären Ordnern und mit kleinen Bildern.
- Für den Abbruch mitten im Job ersetzt der Test den Rechenkern durch
  eine Funktion, die eine Ausnahme auslöst, wie sie Strg+C auslöst.
- Der Autostart-Ordner wird im Test über die Umgebungsvariable `APPDATA`
  auf einen temporären Ordner gelenkt.

## Zuordnung von Abnahme und Nachweis

| Kriterium | Nachweis |
| --- | --- |
| C1, C2, C3 | `test_arbeiter`, dazu einmal von Hand auf Richards PC |
| C4 | Richard öffnet am iPad `http://<Adresse des PCs>:8000/docs` |
| C5 | `test_jobs`, `test_server` |
| C6 | `test_arbeiter`, `test_abnahme_3`, Blick in `_EVENTS` |
| C7 | nur auf Richards PC prüfbar |
| C8 | `python -m pytest` |
| C9 | `git tag stufe-3` nach der Abnahme |

## Stand des Baus

Stufe 3 wird in zwei Teilen gebaut, weil in der Bauumgebung `fastapi` fehlt
(Punkt T6).

| Teil | Inhalt | Stand |
| --- | --- | --- |
| A | `einstellungen`, `jobs`, `warteschlange`, `protokoll`, `arbeiter`, `autostart`, Befehle `arbeiter` und `autostart`, die Tests dazu | gebaut und getestet am 16.11.2026 |
| B | `server`, Befehle `server` und `start`, `test_server`, `test_abnahme_3`, neue Abhängigkeiten in `requirements.txt` | steht aus |

Solange Teil B fehlt, ruft die Autostart-Datei einen Befehl auf, den es
noch nicht gibt. Stufe 3 kommt deshalb erst mit Teil B nach `main`.

### Präzisierungen beim Bauen von Teil A

1. Der Weg von Abbruchwerten zu Farbstufen steht als `bilde_farbstufen` in
   `statistik.py`. Befehl `berechne` und Arbeiter benutzen dieselbe
   Funktion.
2. Das Lebenszeichen hat ein drittes Feld `beendet`. Endet der Arbeiter
   ordentlich, meldet der Job-Server ihn sofort als nicht aktiv.
3. Die Autostart-Datei wartet von sich aus, bis der Projektordner
   erreichbar ist. Punkt T8 ist damit vorweggenommen.
4. Eine Job-Datei darf mit der Kennung beginnen, die der Editor von Windows
   an den Anfang von UTF-8-Dateien setzt.
5. Das Feld `name` ist in einer Job-Datei nicht erlaubt. Der Name ist der
   Dateiname. Beim Anlegen über den Job-Server steht `name` nur in der
   Anfrage.
6. Dazugekommen sind `tests/stufe3.py` mit Hilfen für die Tests und
   `tests/test_einstellungen.py`.

Eine bekannte Grenze: Wird der Arbeiter hart beendet, etwa durch
Stromausfall, steht im Lebenszeichen weiter der laufende Job. Der
Job-Server meldet den Arbeiter dann als aktiv, bis er neu gestartet wird.

## Nicht in dieser Stufe

- Zugriff der Web-App von einer anderen Adresse aus (CORS). Das klärt
  Stufe 4.
- Ein Windows-Dienst. Der Autostart läuft beim Anmelden, nicht beim
  Hochfahren.
- Sperren für mehrere Arbeiter.
- Aufrufe zum Löschen oder Ändern.

## Offene technische Punkte

| Nr. | Frage | Vorschlag |
| --- | --- | --- |
| T6 | In der Bauumgebung fehlen `fastapi` und `httpx`, und Installationen sind dort gesperrt. | Thorsten erlaubt Paketinstallationen. Bis das wirkt, lassen sich Jobs, Warteschlange, Arbeiter, Protokoll und Autostart bauen und testen, der Job-Server nicht. |
| T7 | Fragt die Windows-Firewall beim ersten Start des Job-Servers nach? | Vermutlich ja. Richard erlaubt den Zugriff für private Netze. Der Schritt kommt ins README. |
| T8 | Ist das Laufwerk X: beim Anmelden schon verbunden, wenn der Autostart läuft? | Die Autostart-Datei wartet, bis der Projektordner erreichbar ist. Auf Richards PC prüfen. |
