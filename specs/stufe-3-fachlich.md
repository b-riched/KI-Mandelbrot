# Stufe 3: Jobs und Server – fachliche Spec

Status: freigegeben von Thorsten am 16.11.2026. Richard hat die Entscheidungen H1 bis H6 am 18.11.2026 freigegeben. Teil C (R27, H7 bis H9, C10) ist ein Entwurf vom 23.11.2026 und wartet auf die Freigabe.
Stand: 23.11.2026
Übergeordnet: [Stufenkonzept](stufenkonzept.md)
Gegenstück: [technische Spec](stufe-3-technisch.md)
Baut auf: [Stufe 2a](stufe-2a-fachlich.md)

## Ziel

Jede Berechnung wird durch eine Job-Datei beschrieben. Der PC arbeitet die
Warteschlange selbständig ab und legt die Ergebnisse ab. Über einen
Job-Server lassen sich im Heimnetz Jobs anlegen und Ergebnisse abrufen, auch
vom iPad. Eine Bedienoberfläche gibt es noch nicht, die kommt in Stufe 4.

## Begriffe

| Begriff | Bedeutung |
| --- | --- |
| Job | Der Auftrag, ein Bild zu rechnen. Eine Datei mit Mittelpunkt, Bildbreite, Bildgröße und weiteren Angaben. |
| Warteschlange | Alle Jobs, die noch nicht gerechnet sind, in der Reihenfolge ihres Eingangs. |
| Arbeiter | Das Programm auf dem PC, das die Warteschlange abarbeitet. |
| Job-Server | Das Programm auf dem PC, über das andere Geräte im Heimnetz Jobs anlegen und Ergebnisse abrufen. |
| Ergebnis | Der Lauf-Ordner, der aus einem Job entsteht, wie in Stufe 2a. |
| Elternbild | Das Ergebnis, aus dem ein Ausschnitt gewählt wurde. Grundlage für die Zoom-Kette in Stufe 4 und die Videos in Stufe 6. |
| Serie | Ein frei wählbarer Name, der zusammengehörige Jobs verbindet. |
| Protokoll | Die Aufzeichnung dessen, was mit jedem Job geschehen ist. |

## Was man nach Stufe 3 tun kann

1. **Einen Job als Datei ablegen.** Die Datei kommt in den Ordner für neue
   Jobs. Der Arbeiter rechnet sie, und das Ergebnis liegt im Ergebnisordner.
2. **Einen Job über das Heimnetz anlegen.** Vom iPad oder einem anderen
   Rechner aus, über die Adresse des PCs.
3. **Den Stand abfragen.** Welche Jobs warten, welcher läuft, welche sind
   fertig, welche sind gescheitert und warum.
4. **Ergebnisse abrufen.** Bild und Beschreibung jedes fertigen Jobs.
5. **Nachlesen, was geschehen ist.** Im Protokoll.
6. **Einen Job vormerken und später starten.** Ein geplanter Job wartet,
   bis er freigegeben wird. Erst dann kommt er in die Warteschlange.

## Fachregeln

Die Regeln R1 bis R16 gelten weiter. Neu sind R17 bis R27. R27 ist am
23.11.2026 mit dem überarbeiteten Stufenkonzept dazugekommen (Teil C).

### R17 Ordner

Alle Ordner liegen im Projektordner auf dem Server.

| Ordner | Inhalt |
| --- | --- |
| `_JOBS/geplant` | vorgemerkte Jobs, die noch nicht gerechnet werden (R27) |
| `_JOBS/neu` | Jobs, die auf die Berechnung warten |
| `_JOBS/laeuft` | der Job, der gerade gerechnet wird |
| `_JOBS/fertig` | gerechnete Jobs |
| `_JOBS/fehler` | gescheiterte Jobs, jeder mit einer Datei, die den Grund nennt |
| `_ERGEBNISSE/<Jobname>` | das Ergebnis eines Jobs |
| `_EVENTS` | das Protokoll |

Die Ordner werden nicht ins Repo eingecheckt. Fehlt einer, legt das
Programm ihn an. Die Namen lassen sich in einer Einstellungsdatei ändern.

### R18 Job

Ein Job ist eine Datei `<Jobname>.json`. Der Jobname ist der Dateiname ohne
Endung. Er muss unter allen Jobs und Ergebnissen einmalig sein.

| Angabe | Pflicht | Bedeutung | Ohne Angabe |
| --- | --- | --- | --- |
| `mitte_x`, `mitte_y` | ja | Mittelpunkt als Dezimaltext | – |
| `breite` | ja | Bildbreite als Dezimaltext | – |
| `groesse` | siehe R19 | `hd`, `fullhd`, `wqhd`, `ipad` oder `BREITExHÖHE` | Größe des Elternbildes |
| `abbruchgrenze` | nein | 10 bis 1.000.000 | 1005 |
| `palette` | nein | 0 bis 3 | 1 |
| `schwelle` | nein | ganze Zahl ab 0 oder `auto` | `auto` |
| `max_bereiche` | nein | 1 bis 256 | 255 |
| `elternbild` | nein | Jobname des Ergebnisses, aus dem der Ausschnitt stammt | kein Elternbild |
| `serie` | nein | frei wählbarer Name | keine Serie |
| `notiz` | nein | freier Text | leer |

Eine Angabe, die nicht in dieser Tabelle steht, ist ein Fehler. So fallen
Tippfehler auf.

### R19 Bildgröße eines Jobs

Das ist Richards Entscheidung aus dem Stufenkonzept:

- Ist eine Bildgröße angegeben, gilt sie.
- Ist keine angegeben und hat der Job ein Elternbild, gilt die Größe des
  Elternbildes.
- Ist keine angegeben und gibt es kein Elternbild, ist der Job fehlerhaft.
  Über den Job-Server wird er gar nicht erst angelegt.

### R20 Reihenfolge

- Es läuft immer nur ein Job.
- Der Arbeiter nimmt den ältesten Job aus `_JOBS/neu`. Maßgeblich ist der
  Zeitpunkt, zu dem der Job angelegt wurde. Bei einem freigegebenen Job
  zählt der Zeitpunkt der Freigabe (R27).
- Jobs in `_JOBS/geplant` fasst der Arbeiter nicht an.
- Eine Datei, die gerade erst geschrieben wird, bleibt zwei Sekunden
  liegen, bevor der Arbeiter sie anfasst.

### R21 Ablauf eines Jobs

1. Der Job wandert von `neu` nach `laeuft`.
2. Der Arbeiter prüft die Angaben nach R18, R19 und R15.
3. Er rechnet, bildet die Farbstufen und färbt ein, wie in Stufe 2a.
4. Das Ergebnis liegt vollständig unter `_ERGEBNISSE/<Jobname>`. Die
   Beschreibung des Laufs nennt zusätzlich Jobname, Elternbild, Serie und
   die Zeiten für Anlegen, Start und Ende.
5. Der Job wandert nach `fertig`.

Ein Ergebnis erscheint erst im Ergebnisordner, wenn es vollständig ist.
Halbe Ergebnisse sind von außen nicht sichtbar.

### R22 Fehler

- Ist ein Job fehlerhaft, wandert er nach `_JOBS/fehler`. Daneben liegt
  eine Textdatei `<Jobname>.fehler.txt` mit dem Grund, auf Deutsch.
- Der Arbeiter macht danach mit dem nächsten Job weiter.
- Gibt es zu einem Jobnamen schon ein Ergebnis, ist das ein Fehler. Ein
  vorhandenes Ergebnis wird nie überschrieben.
- Eine Warnung nach R15 ist kein Fehler. Sie steht im Protokoll und in der
  Beschreibung des Laufs.

### R23 Neustart

Wird der PC oder der Arbeiter mitten in einem Job beendet, geht der Job
nicht verloren. Beim nächsten Start wandert er von `laeuft` zurück nach
`neu` und wird neu gerechnet. Reste eines halben Ergebnisses werden vorher
entfernt.

### R24 Job-Server

Der Job-Server ist im Heimnetz unter der Adresse des PCs erreichbar, ohne
Anmeldung. Er kann:

- einen Job anlegen, wahlweise gleich in die Warteschlange oder als
  geplanten Job. Ein fehlerhafter Job wird mit einer Meldung abgewiesen und
  nicht angelegt.
- einen geplanten Job freigeben (R27).
- alle Jobs mit ihrem Stand auflisten und einen einzelnen Job zeigen, bei
  gescheiterten mit dem Grund.
- alle Ergebnisse auflisten.
- Beschreibung und Bild eines Ergebnisses ausliefern.
- den Zustand melden: wie viele Jobs in jedem Ordner liegen und ob der
  Arbeiter läuft.

Der Job-Server rechnet nicht selbst. Er legt Jobs nur in die Warteschlange.
Er bringt eine Testseite mit, auf der sich alle Funktionen im Browser
ausprobieren lassen. Sie ersetzt bis Stufe 4 die Bedienoberfläche.

### R25 Protokoll

Das Protokoll liegt in `_EVENTS`, eine Textdatei pro Tag. Jede Zeile nennt
Zeitpunkt, Jobname, Ereignis und einen kurzen Text. Festgehalten werden:

- Job angelegt (über den Job-Server) oder entdeckt (als Datei abgelegt),
- geplanter Job freigegeben,
- Job gestartet,
- Job fertig, mit Rechenzeit,
- Job gescheitert, mit Grund,
- Job nach einem Neustart zurückgestellt,
- Warnungen nach R15,
- Start und Ende von Arbeiter und Job-Server.

### R27 Geplante Jobs

Das ist die Ergänzung aus dem Stufenkonzept vom 22.11.2026. Der
MandelManager in Stufe 4 legt einen gewählten Ausschnitt zuerst als
geplanten Job an. Erst „Starten" schickt ihn in die Warteschlange.

- Ein geplanter Job liegt in `_JOBS/geplant`. Er ist ein vollständiger Job
  nach R18 und R19 und wird beim Anlegen genauso geprüft.
- Der Arbeiter rechnet ihn nicht. Er bleibt liegen, bis er freigegeben
  wird, auch über Neustarts hinweg.
- Die Freigabe schiebt ihn nach `_JOBS/neu`. Vorher wird er noch einmal
  nach R18, R19 und R15 geprüft. Scheitert die Prüfung, bleibt er in
  `geplant`, und die Freigabe meldet den Grund.
- Nur ein Job in `geplant` lässt sich freigeben. Für einen Job in einem
  anderen Stand meldet die Freigabe, wo er gerade liegt.
- Wer eine Datei von Hand von `geplant` nach `neu` verschiebt, gibt sie
  damit ebenfalls frei. Im Protokoll fehlt dann der Eintrag „freigegeben".
- Ein geplanter Job belegt seinen Namen wie jeder andere Job (R18).

### R26 Starten und Autostart

- Ein Befehl startet Arbeiter und Job-Server zusammen. Beide lassen sich
  auch einzeln starten.
- Ob beide beim Anmelden am PC von selbst anlaufen, ist einstellbar. Ein
  Befehl schaltet den Autostart an und aus. Das ist Richards Entscheidung
  aus dem Stufenkonzept.

## Nicht in dieser Stufe

- Bedienoberfläche, Galerie, Ausschnittwahl (Stufe 4).
- Jobs abbrechen, löschen oder umsortieren. Das gilt auch für geplante
  Jobs (H9).
- Mehrere Arbeiter gleichzeitig, mehrere PCs.
- Anmeldung und Zugriff von außerhalb des Heimnetzes.
- Rechnen auf der Grafikkarte (Stufe 2b). Der Arbeiter benutzt sie später
  von selbst, ohne dass sich an den Jobs etwas ändert.
- Jobs zum Neu-Einfärben (Stufe 5) und Serien-Jobs für Videos (Stufe 6).
  Die Angabe `serie` wird in Stufe 3 nur gespeichert.
- Jobs in der Form wie 1991 (xmin, xmax, ymin, ymax).
- Aufräumen alter Jobs und Ergebnisse.

## Entscheidungen

Thorsten hat am 16.11.2026 alle sechs Vorschläge übernommen. Richard hat
die Entscheidungen H1 bis H6 am 18.11.2026 freigegeben. Damit ist auch H1
bestätigt, das bis dahin offen war. Der Ordner der Ergebnisse bleibt
einstellbar.

| Nr. | Frage | Entschieden wie vorgeschlagen |
| --- | --- | --- |
| H1 | Wo liegen die Ergebnisse? | In `_ERGEBNISSE` im Projektordner, neben `_JOBS` und `_EVENTS`. |
| H2 | Reichen die vier Unterordner `neu`, `laeuft`, `fertig`, `fehler` in `_JOBS`? | Ja. |
| H3 | Ist der Jobname der Dateiname? | Ja. Über den Job-Server angelegte Jobs ohne Namen heißen `job-JJJJMMTT-HHMMSS`. |
| H4 | Soll ein unbekanntes Feld im Job ein Fehler sein? | Ja, damit Tippfehler auffallen. |
| H5 | Unter welcher Portnummer läuft der Job-Server? | 8000, einstellbar. |
| H6 | Wie soll der Autostart arbeiten? | Über den Autostart-Ordner von Windows, also beim Anmelden. Voraussetzung: Das Laufwerk X: ist dann schon verbunden. |

H2 ist mit dem Stufenkonzept vom 22.11.2026 überholt: Zu den vier
Unterordnern kommt `geplant` (R27).

### Entscheidungen zu Teil C

Vorschläge vom 23.11.2026. Sie warten auf die Freigabe durch Thorsten und
Richard.

| Nr. | Frage | Vorschlag |
| --- | --- | --- |
| H7 | Wohin legt der Job-Server einen neuen Job, wenn die Anfrage nichts dazu sagt? | Nach `neu`, also gleich in die Warteschlange, wie bisher. Mit der Angabe `"geplant": true` landet er in `geplant`. So bleiben Testseite und bisherige Abläufe gleich. Der MandelManager schickt ab Stufe 4 immer `"geplant": true`. |
| H8 | Wann reiht sich ein freigegebener Job in die Warteschlange ein? | Zum Zeitpunkt der Freigabe. Sonst überholt ein vor Tagen geplanter Job alle Jobs, die schon warten. |
| H9 | Lässt sich ein geplanter Job über den Job-Server verwerfen? | Nicht in Stufe 3. Bis dahin löscht man die Datei in `_JOBS/geplant` von Hand. Den Aufruf bekommt der MandelManager in Stufe 4, wenn er ihn braucht. |

## Abnahme

- [ ] **C1** Eine von Hand in `_JOBS/neu` gelegte Job-Datei wird gerechnet.
      Das Ergebnis liegt in `_ERGEBNISSE`, der Job in `_JOBS/fertig`.
- [ ] **C2** Ein fehlerhafter Job landet mit lesbarer Meldung in
      `_JOBS/fehler`, und der nächste Job wird trotzdem gerechnet.
- [ ] **C3** Nach einem Neustart mitten in einem Job wird dieser Job neu
      gerechnet und geht nicht verloren.
- [ ] **C4** Vom iPad aus lässt sich über die Adresse des PCs ein Job
      anlegen, sein Stand abfragen und das fertige Bild ansehen.
- [ ] **C5** Ein Job ohne Bildgröße bekommt die Größe seines Elternbildes.
      Ohne Bildgröße und ohne Elternbild wird er abgewiesen.
- [ ] **C6** Das Protokoll nennt für jeden Job Anlegen, Start und Ende
      oder Fehler.
- [ ] **C7** Der Autostart lässt sich auf Richards PC an- und ausschalten.
      Nach dem Anmelden laufen Arbeiter und Job-Server von selbst.
- [ ] **C8** Alle Tests aus den Stufen 1 und 2a laufen unverändert durch.
- [ ] **C9** Der Stand trägt die Marke `stufe-3`.
- [ ] **C10** Ein Job in `_JOBS/geplant` wird nicht gerechnet, bevor er
      freigegeben ist, und nach der Freigabe läuft er. Das Kriterium kommt
      aus dem Stufenkonzept vom 22.11.2026. Die Marke nach C9 wird erst
      gesetzt, wenn auch C10 erfüllt ist.

## Ergebnis für die nächsten Stufen

- **Stufe 4** findet einen Job-Server vor, über den die Web-App Jobs
  plant, freigibt, den Stand abfragt und Bilder lädt. Jedes Ergebnis kennt
  sein Elternbild.
- **Stufe 2b** tauscht nur den Rechenkern. Jobs, Arbeiter und Job-Server
  bleiben, wie sie sind.
- **Stufe 6** kann zusammengehörige Jobs über die Serie finden.
