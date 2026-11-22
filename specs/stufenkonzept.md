# KI-Mandelbrot: Stufenkonzept

Stand: 22.11.2026 · Überarbeitete Version unter Berücksichtigung der Kommentare aus Review (PullRequest #7)

Änderungen gegenüber dem Stand vom 12.11.2026: MandelManager (MM) als Bedienoberfläche eingeführt. Stufe 4 wird zur Bildwahl im MM, Stufe 5 wird in 5a (Einfärber) und 5b (Farb-Editor) geteilt, Stufe 6 bekommt einen Pfad-Editor im MM. Stufe 3 bekommt den Job-Status `geplant`. Die Originalpaletten sind auf drei verschiedene berichtigt.

## Zweck und Arbeitsweise

Jede Stufe wird erst spezifiziert, dann gebaut, dann abgenommen. Die nächste Stufe beginnt erst nach der Abnahme der vorigen.

Ausnahme seit dem 16.11.2026: Eine Stufe darf spezifiziert und gebaut werden, bevor die vorige abgenommen ist. In `main` kommt sie erst nach deren Abnahme. Ändert die Abnahme etwas an der vorigen Stufe, wird die spätere nachgezogen.

Dieses Dokument ist das Dach über allen Stufen. Es legt fest, was jede Stufe liefert und woran wir erkennen, dass sie fertig ist. Die Detail-Spec einer Stufe entsteht erst, wenn sie an der Reihe ist.

Ablauf pro Stufe:

1. **Spec schreiben.** Eine Datei `specs/stufe-N.md` im Repo mit Ziel, Umfang, Nicht-Umfang, Schnittstellen und Abnahmekriterien.
2. **Spec freigeben.** Richard und Thorsten lesen sie und sagen ja oder ändern sie.
3. **Bauen.** Claude baut genau das, was in der Spec steht, nicht mehr.
4. **Abnehmen.** Die Abnahmekriterien werden einzeln geprüft. Der abgenommene Stand bekommt im Repo die Marke `stufe-N`.
5. **Funde parken.** Was beim Bauen auffällt und nicht in der Spec steht, kommt in die Spec einer späteren Stufe oder in die offenen Punkte, nicht in den Code.

Der Abschnitt „Nicht in dieser Stufe“ ist bei jeder Stufe genauso verbindlich wie der Umfang. Er ist der Schutz davor, im Wald zu landen.

## Festgelegte Grundentscheidungen

Diese Punkte sind entschieden und gelten für alle Stufen. Wer einen davon ändern will, ändert zuerst dieses Dokument.

| Thema | Festlegung |
| --- | --- |
| Rechenkern | Python mit Numba-CUDA. Variante: CuPy mit der Rechenschleife in CUDA-C. |
| Grafikkarte | RTX 3080 Ti, eingebaut. Die RTX 4070 Ti Super bleibt als Alternative. |
| Job-Server | Python mit FastAPI, läuft auf dem Windows-PC. |
| Server FNSERVER001 | Nur Dateiablage für Jobs und Ergebnisse. |
| Bedienung | Der MandelManager (MM): eine Web-App in TypeScript, die der Job-Server ausliefert. Sie läuft im Browser auf PC, Mac und iPad. Unter Windows startet eine Verknüpfung sie als eigenes Anwendungsfenster ohne Adressleiste. Eine echte native Windows-App ist eine eigene Stufe. |
| Rechnen und Einfärben | Alles, was Bilder erzeugt, läuft auf dem Server (PC). Der Browser zeigt nur an, auch bei der Vorschau beim Einfärben. |
| Netz | Nur Heimnetz. Ein VPN richtet Richard bei Bedarf selbst ein. |
| Zoomtiefe Stufen 1 bis 6 | Bis etwa 10⁻¹² Bildbreite. Tiefer erst in Stufe 7. |
| Ausgabeformate | Bilder als PNG (24 Bit ab Stufe 5a), Videos als MP4, Metadaten als JSON. |
| Koordinaten | Als Dezimaltext mit beliebig vielen Stellen, nie als gerundete Zahl. |
| Originale | `Org_Daten` bleibt unverändert im Repo. In `Org_Sourcen` sind vier Dateien seit dem 16.11.2026 nach UTF-8 umkodiert, damit die Umlaute lesbar sind. Das bleibt so (Entscheidung vom 18.11.2026). Die Fassungen von 1991 liegen im Commit `af67afa`. |
| Nachweis der Abnahme | Jede abgenommene Stufe bekommt die Marke `stufe-N` auf dem geprüften Stand (bestätigt am 18.11.2026). Ein Branch reicht nicht, weil er weiterwandert. |
| Repo | [b-riched/KI-Mandelbrot](https://github.com/b-riched/KI-Mandelbrot) |

## Stufenübersicht

Zehn Stufen, jede mit einem vorzeigbaren Ergebnis. Nach Stufe 4 ist Richards Kreislauf von 1991 wieder geschlossen: rechnen, ansehen, Ausschnitt wählen, neu rechnen.

| Stufe | Name | Ergebnis | Baut auf |
| --- | --- | --- | --- |
| 0 | Fundament | Repo-Struktur steht, Originale sind geschützt und dokumentiert | – |
| 1 | Portierung | Richards Pipeline läuft in Python und erzeugt PNG wie 1991 | 0 |
| 2a | Bildgrößen | Bildgröße, Abbruchgrenze und Ausschnitt per Mittelpunkt frei wählbar, auf dem Prozessor | 1 |
| 2b | Grafikkarte | Dieselbe Rechnung auf der Grafikkarte | 2a |
| 3 | Jobs und Server | Jobs liegen als Dateien auf dem Server, der PC arbeitet sie ab | 2a |
| 4 | Web-App: Bildwahl | MandelManager (MM): Bilder ansehen, Ausschnitt wählen, Job planen und starten, auf PC, Mac und iPad | 3 |
| 5a | Farben und Relief | Einfärber ohne Oberfläche: 24-Bit-Verläufe, Höhenlinien, Relief | 2a |
| 5b | Farb-Editor | Verläufe im MM einstellen, Bild dynamisch einfärben, als neue Version speichern | 4 und 5a |
| 6 | Videos | Pfad im MM zeichnen, Zoomfahrt als MP4 | 3, 4 und 5a |
| 7 | Tiefe Zooms | Bildbreiten kleiner als 10⁻¹² | 2b |

Stufe 2 ist seit dem 16.11.2026 geteilt, weil nur der Teil mit der Grafikkarte Richards Rechner braucht. So können Stufe 2a und Stufe 3 gebaut werden, bevor die Grafikkarte an der Reihe ist.

Stufe 5 ist seit dem 20.11.2026 geteilt, weil nur der Editor die Web-App braucht. Stufe 5a braucht nur die Rohdaten aus Stufe 2a. Sie kann deshalb vor Stufe 3 und 4 gezogen werden, wenn Richard früh schöne Bilder sehen will.

## Stufe 0: Fundament

**Ziel:** Das Repo ist so aufgebaut, dass die Originale geschützt sind und jede Stufe ihren festen Platz hat.

**Umfang**

- Ordner `specs/`, `src/`, `tests/` und `docs/` neben `Org_Daten` und `Org_Sourcen`.
- Eine `.gitattributes`, die `*.PAS` und `*.DAT` als unveränderliche Dateien markiert, damit Git keine Zeilenenden umschreibt.
- Ein README mit der Analyse der Originale: die Pipeline aus MANDELDA, MANDELST und MANDELFA, das Format der `.DAT`-Dateien und der Faktor in der Kopfzeile (1000 bei vier Dateien, 10000 bei `M12.DAT`).
- Festgelegte Python-Version und eine Datei mit den Abhängigkeiten.
- Dieses Stufenkonzept als `specs/stufenkonzept.md`.

**Nicht in dieser Stufe:** Kein Code, der rechnet oder Bilder erzeugt.

**Abnahme**

- [ ] `Org_Daten` und `Org_Sourcen` sind byte-gleich zu den Dateien auf Richards Laufwerk.
- [ ] Das README beschreibt das `.DAT`-Format so, dass man die Dateien ohne den Pascal-Quelltext lesen kann.
- [ ] Richard und Thorsten können beide ins Repo schreiben.
- [ ] Die Lizenz des Repos ist gewählt.
- [ ] Alle Abnahmekriterien sind erfüllt aus `specs/stufe-0.md`.

## Stufe 1: Portierung

**Ziel:** Richards drei Programme laufen als Python-Module auf dem Prozessor und liefern PNG-Bilder, die den Bildern von 1991 entsprechen.

**Umfang**

- **Berechnen** (aus MANDELDA): Abbruchwerte für 480 × 480 Punkte, Abbruchgrenze 1005, dieselbe Zuordnung von Bildpunkt zu Koordinate wie im Original.
- **Statistik** (aus MANDELST): Zuordnung der Abbruchwerte auf 255 Farbstufen mit möglichst gleich großen Farbbereichen. Der Schwellenwert ist ein Parameter statt einer Abfrage am Bildschirm.
- **Paletten** (aus MANDPAL): die vier Originalpaletten. Palette 0 und 2 sind identisch, es gibt also drei verschiedene.
- **Leser** für die fünf Original-`.DAT`-Dateien einschließlich des richtigen Kopfzeilen-Faktors.
- **Ausgabe** als PNG, dazu Rohdaten und eine JSON-Datei mit den Koordinaten als Dezimaltext.
- Aufruf über die Kommandozeile.

**Nicht in dieser Stufe:** Grafikkarte, andere Bildgrößen, neue Farben, jede Art von Bedienoberfläche. MANDELMO (eigene Formel) und MANDMAUS (Fragment) werden nicht portiert.

**Abnahme**

- [ ] Alle fünf Original-`.DAT`-Dateien werden gelesen und als PNG ausgegeben.
- [ ] Für jeden der fünf Ausschnitte stimmt die neu berechnete Menge mit der Originaldatei überein, mindestens so gut wie in der Voranalyse: `M0` 99,9 %, `M01` 99,9 %, `M1` 99,9 %, `M11` 97,8 %, `M12` 99,9 %.
- [ ] Richard vergleicht je ein neu berechnetes Bild mit dem Original und nimmt es ab.
- [ ] Alle Tests laufen mit einem einzigen Befehl.

Die Abweichung bei `M11` kommt vermutlich von den gerundeten Koordinaten in der alten Kopfzeile, nicht von der Rechnung.

## Stufe 2a: Bildgrößen und freier Ausschnitt

**Ziel:** Bildgröße, Abbruchgrenze und Ausschnitt sind frei wählbar. Gerechnet wird auf dem Prozessor.

**Umfang**

- Ein Ausschnitt wird durch Mittelpunkt und Bildbreite beschrieben. Die Bildhöhe ergibt sich aus dem Seitenverhältnis, die Bildpunkte bleiben quadratisch.
- Bildgrößen 1280 × 720, 1920 × 1080, 2560 × 1440 und 2360 × 1640, dazu jede frei gewählte Größe.
- Abbruchgrenze als Parameter.
- Zusätzlich zu den ganzen Abbruchwerten werden gebrochene Abbruchwerte gespeichert. Sie sind die Grundlage für stufenlose Farben in Stufe 5a.
- Warnung, wenn die Bildbreite unter 10⁻¹² liegt.

**Nicht in dieser Stufe:** Grafikkarte, Störungsrechnung, Jobs, Farben.

**Abnahme**

- [ ] Je ein Bild in den vier benannten Größen und in einer freien Größe ist gerechnet.
- [ ] Alle Tests aus Stufe 1 laufen unverändert durch.
- [ ] Ein Bild mit 10⁻¹² Bildbreite in 2560 × 1440 zeigt keine Klötzchen.
- [ ] Alle Abnahmekriterien sind erfüllt aus `specs/stufe-2a-fachlich.md`.

## Stufe 2b: Grafikkarte

**Ziel:** Der Rechenkern läuft auf der RTX 3080 Ti und liefert dasselbe wie der Prozessor.

**Umfang**

- Rechenschleife mit Numba-CUDA in doppelter Genauigkeit.
- Derselbe Aufruf rechnet auf dem Prozessor, wenn keine Grafikkarte da ist.

**Nicht in dieser Stufe:** Störungsrechnung. Die CuPy-Variante wird nur gebaut, wenn Numba an eine Grenze stößt.

**Abnahme**

- [ ] Grafikkarte und Prozessor liefern für denselben Ausschnitt in mindestens 99,9 % der Punkte denselben ganzen Abbruchwert.
- [ ] Die Rechenzeiten für die vier Bildgrößen sind auf Richards PC gemessen und in der Spec eingetragen.
- [ ] Die Installation auf Richards PC ist als Schrittfolge im README beschrieben und einmal von ihm durchgespielt.

## Stufe 3: Jobs und Server

**Ziel:** Jede Berechnung wird über eine Job-Datei gesteuert, und der PC arbeitet die Warteschlange selbständig ab.

**Umfang**

- **Job-Format** als JSON: Mittelpunkt und Bildbreite als Dezimaltext, Bildgröße, Abbruchgrenze, Palette, Elternbild und Serie.
- **Ordner:** `_JOBS/geplant`, `_JOBS/neu`, `_JOBS/laeuft`, `_JOBS/fertig`, `_JOBS/fehler` und `_ERGEBNISSE/<Jobname>/` mit Rohdaten, PNG und Metadaten. Ein Job in `geplant` wird nicht gerechnet. Erst die Freigabe verschiebt ihn nach `neu`. (Ergänzung vom 20.11.2026, wird in Stufe 3 nachgezogen.)
- **Arbeiter** auf dem PC: holt den ältesten Job aus `_JOBS/neu`, rechnet, färbt ein, legt das Ergebnis ab.
- **Job-Server** auf dem PC: Job anlegen (nach `geplant` oder `neu`), geplanten Job freigeben, Jobs mit Status auflisten, Bilder und Metadaten ausliefern.

**Nicht in dieser Stufe:** Bedienoberfläche, Anmeldung, Zugriff von außerhalb des Heimnetzes, mehrere Arbeiter gleichzeitig.

**Abnahme**

- [ ] Eine von Hand in `_JOBS/neu` gelegte Job-Datei wird gerechnet, und das Ergebnis liegt im Ergebnisordner.
- [ ] Ein Job in `_JOBS/geplant` wird nicht gerechnet, bevor er freigegeben ist, und nach der Freigabe läuft er.
- [ ] Ein fehlerhafter Job landet mit lesbarer Meldung in `_JOBS/fehler`, und die Warteschlange läuft weiter.
- [ ] Nach einem Neustart des PCs mitten in einem Job wird dieser Job neu gerechnet und geht nicht verloren.
- [ ] Vom iPad aus lässt sich über die Adresse des PCs im Heimnetz ein Job anlegen und sein Status abfragen.

## Stufe 4: Web-App (MandelManager, Bildwahl)

**Ziel:** Richard kann am PC, am Mac und am iPad Bilder ansehen, den nächsten Ausschnitt wählen und daraus einen Job planen und starten. Das ist der MandelManager (MM), den die Stufen 5b und 6 erweitern.

**Umfang**

- **Zwei Bereiche:** Bildansicht und Bedienkonsole. Am PC lässt sich die Konsole als eigenes Fenster abdocken und auf einen anderen Monitor ziehen, während das Bild den Hauptmonitor füllt. Am iPad bleibt sie ein Seitenbereich neben dem Bild. Beide Bereiche zeigen denselben Stand (Bild, Auswahl).
- **Galerie** aller fertigen Bilder, neueste zuerst.
- **Bildansicht** mit Vergrößern und Verschieben.
- **Ausschnittwahl:** Ein Rahmen im Seitenverhältnis des Bildes, das entstehen soll. Position und Breite sind per Maus oder Finger frei wählbar. Alternativ gibt man `mitte_x`, `mitte_y` und Breite als Dezimaltext in der Konsole ein. Der Rahmen erscheint dann im Bild und lässt sich weiter verschieben, die Zahlen folgen.
- **Job planen:** „Übernehmen“ legt eine Job-Datei in `_JOBS/geplant` ab. Das Bild, in dem gewählt wurde, wird als Elternbild eingetragen. Ein abgeleitetes Bild hat immer dasselbe Seitenverhältnis wie sein Elternbild, voreingestellt auch dieselbe Bildgröße. Ohne Elternbild ist das Format frei wählbar. Dazu kommen Abbruchgrenze und Palette. Bei Bildbreite unter 10⁻¹² erscheint eine Warnung.
- **Job-Liste** mit Status (geplant, neu, läuft, fertig, Fehler), die sich selbst aktualisiert. Ein geplanter Job wird mit „Starten“ freigegeben.
- **Zoom-Kette:** Jedes abgeleitete Bild kennt sein Elternbild. Das ist die Grundlage für die Videos in Stufe 6.
- Auf dem iPad lässt sich die Web-App auf den Home-Bildschirm legen.

**Nicht in dieser Stufe:** Berechnung im Browser, Einfärben und Farbverläufe (Stufe 5b), Pfade und Videos (Stufe 6), Anmeldung, native App, Zugriff von außen.

**Abnahme**

- [ ] Am iPad: Bild öffnen, Ausschnitt wählen, Job planen, starten, das fertige Bild erscheint in der Galerie.
- [ ] Derselbe Ablauf am PC mit der Maus.
- [ ] Mit eingegebenen Zahlen entsteht derselbe Rahmen wie von Hand gezogen, und das neue Bild zeigt genau ihn.
- [ ] Am PC mit zwei Monitoren: Die Konsole liegt auf dem zweiten Monitor, das Bild füllt den ersten.
- [ ] Ohne Elternbild und ohne gewählte Bildgröße wird kein Job angelegt, die Fehlermeldung ist lesbar.
- [ ] Von jedem abgeleiteten Bild führt ein Klick zum Elternbild.

## Stufe 5a: Farben und Relief (Einfärber)

**Ziel:** Der Einfärber erzeugt aus gespeicherten Rohdaten Bilder mit stufenlosen Farbverläufen, Höhenlinien und Relief, ohne neu zu rechnen.

**Umfang**

- **PNG-24:** 8 Bit pro Farbkanal. Richards drei verschiedene Originalpaletten werden als Farbverläufe bzw. als Farbschema übernommen.
- **Zuordnung** der gebrochenen Abbruchwerte auf den Verlauf, wählbar: Richards Statistik-Verfahren, linear oder logarithmisch. Die Gruppen gleicher Farbe entfallen, weil der Verlauf stufenlos ist. Die Verteilung der Abbruchwerte bleibt aber nutzbar, damit die Farben nicht in wenigen Werten verklumpen.
- **Farbverläufe** Farbschemata werden als kleine Textdateien mit Stützfarben und Positionen.
- **Höhenlinien** (Linien gleicher Abbruchwerte) mit einstellbarem Abstand und einstellbarer Farbe.
- **Relief-Schattierung** mit einstellbarer Lichtrichtung und Färbung.
- Höhenlinien und Relief sind einzeln ein- und ausschaltbar.
- **Neu einfärben** als eigener Job-Typ. Das Ergebnis ist eine neue Version des Bildes. Die Rohdaten und die früheren Versionen bleiben erhalten.

**Nicht in dieser Stufe:** Oberfläche und Farb-Editor (Stufe 5b).

**Abnahme**

- [ ] Ein vorhandenes Ergebnis wird neu eingefärbt, ohne dass der Rechenkern läuft.
- [ ] In ruhigen Bildbereichen sind keine Farbstufen zu sehen.
- [ ] Höhenlinien und Relief lassen sich einzeln ein- und ausschalten.
- [ ] Richard nimmt je ein Bild mit jeder der drei Originalpaletten ab und hat mindestens drei Verläufe als Standard ausgewählt.

## Stufe 5b: Farb-Editor im MandelManager (MM)

**Ziel:** Richard stellt Farben im MM ein und sieht das Bild dabei dynamisch umgefärbt.

**Umfang**

- **Ein Bild einfärben:** Ein Bild laden und einen gespeicherten Verlauf wählen. Die vorhandenen Schemata stehen zur Auswahl.
- **Eigener Verlauf:** Richard markiert Bildbereiche per Maus oder Finger und wählt für jeden eine Farbe aus einem Farbkreis. Der MM verteilt die Zwischenfarben anhand der normalisierten Stufenverteilung im Bild.
- **Dynamische Vorschau** beim Einstellen. Sie wird auf dem Server aus verkleinerten Rohdaten gerechnet, damit Vorschau und Ergebnis dieselbe Implementierung nutzen.
- **Relief:** Lichtrichtung grafisch einstellbar, dazu Färbung. 
- **Höhenlinien:** Abstand wählbar. Beide einzeln schaltbar.
- **Speichern:** Der Verlauf bekommt einen Namen und steht künftig zur Auswahl. Das umgefärbte Bild wird über den Einfärber (Stufe 5a) als neue Version gespeichert.

**Nicht in dieser Stufe:** Neu berechnen, Bildbearbeitung außerhalb der Farben, Rechnung im Browser.

**Abnahme**

- [ ] Am iPad und am PC: Bild laden, Farben aus dem Farbkreis zuweisen, die Vorschau reagiert ohne spürbare Wartezeit.
- [ ] Der gespeicherte Verlauf ist beim nächsten Start wählbar.
- [ ] Die gespeicherte Version stimmt mit der Vorschau überein.
- [ ] Relief und Höhenlinien lassen sich einzeln ein- und ausschalten.

## Stufe 6: Videos

**Ziel:** Aus einem im MM gezeichneten Pfad oder Zielpunkt entsteht eine Zoomfahrt als MP4, wahlweise hinein (Descend) oder heraus (Ascend).

**Umfang**

- **Pfad** im Ausgangsbild: eine Gerade oder eine glatte Kurve. Der Pfad liegt im Parameterraum (Mitte und Bildbreite), nicht in Bildpunkten. Das Ausgangsbild hat das Seitenverhältnis 16:9, alle Schlüsselbilder erben es.
- **Zoomstufe** pro Schlüsselbild wählbar. Voreingestellt ist die halbe Bildbreite des vorigen. Von der Gesamtansicht bis 10⁻¹² sind das bei halber Bildbreite etwa 42 Schlüsselbilder.
- **Anzeige** der Rahmen der nächsten Schlüsselbilder entlang des Pfades, soweit die Auflösung des Ausgangsbildes das zulässt. Reicht sie nicht weiter, wird die Pfaddefinition in einem Detailbild der Serie fortgesetzt.
- **Serien-Job:** Die Auswahl erzeugt wie in Stufe 4 Job-Dateien in `_JOBS/geplant`, eine pro Schlüsselbild, verbunden über die Serie.
- **Zwischenbilder** entstehen durch Zoomen (Vergrößern und Überblenden) benachbarter Schlüsselbilder, nicht durch Neuberechnung. Die Bildmitte folgt dem Pfad.
- **Zeitkurve:** Die Fahrt beginnt langsam, wird schneller und endet langsam.
- **Einheitliche Farbzuordnung** über die ganze Fahrt, damit die Farben nicht flackern.
- **Ausgabe** als MP4 über ffmpeg, in 1920 × 1080.
- Die Ascend-Fahrt nutzt dieselben Schlüsselbilder in umgekehrter Reihenfolge.

**Nicht in dieser Stufe:** Musik (die kommt im Videoschnittprogramm dazu), Drehungen der Kamera, Farbwechsel während der Fahrt.

**Abnahme**

- [ ] Ein Pfad (einmal als Gerade und einmal als Kurve) wird im MM angelegt und erzeugt die Schlüsselbild-Jobs.
- [ ] Eine Fahrt von der Gesamtansicht bis 10⁻¹² liegt als MP4 vor und spielt auf PC und iPad.
- [ ] An den Übergängen zwischen Schlüsselbildern und an Kurven ist kein Sprung zu sehen.
- [ ] Die Farben flackern nicht.
- [ ] Anfang und Ende laufen sichtbar langsamer als die Mitte.
- [ ] Die Ascend-Fassung entsteht ohne neue Berechnung.

## Stufe 7: Tiefe Zooms

**Ziel:** Der Rechenkern liefert fehlerfreie Bilder auch bei Bildbreiten weit unter 10⁻¹².

Die Spec für diese Stufe wird erst nach Stufe 6 geschrieben. Bis dahin gilt nur dieser Rahmen:

- Das Verfahren ist die Störungsrechnung: Ein Bezugspunkt wird hochgenau auf dem Prozessor gerechnet, alle anderen Punkte als kleine Abweichung davon auf der Grafikkarte.
- Am Anfang der Stufe steht eine Entscheidung: Eigenbau oder [Fractalshades](https://gbillotey.github.io/Fractalshades-doc/overview.html) als fertiger Rechenkern hinter unserem Job-Server.
- Job-Format, Einfärber, Web-App und Videobauer bleiben unverändert. Deshalb werden Koordinaten schon ab Stufe 1 als Dezimaltext gespeichert.

**Vorläufige Abnahme**

- [ ] Ein Bild mit 10⁻³⁰ Bildbreite ist fehlerfrei und stimmt mit einem Vergleichsbild aus Fractalshades überein.
- [ ] Eine Zoomfahrt über die alte Grenze von 10⁻¹² hinweg zeigt an dieser Stelle keinen Bruch.

## Offene Punkte

Diese Fragen müssen vor der genannten Stufe beantwortet sein.

| Frage | Vor Stufe |
| --- | --- |
| Welche Lizenz bekommt das Repo? Entschieden: MIT. | 0 |
| Schreibt Claude direkt ins Repo, oder pushen Richard und Thorsten die gelieferten Dateien? Entschieden: per Pull Request. | 0 |
| Gibt es die Units `MOUSE` und `MOUSEWIN` und die Rohdateien `mandelN.dat` noch? Entschieden: MOUSE und MOUSEWIN sind Units aus der Turbo-Pascal-5.5-Bibliothek. Diese stehen nicht mehr zur Verfügung. | 1 |
| Wie viele Originalpaletten gibt es? Entschieden: vier, davon sind Palette 0 und 2 identisch, es bleiben drei verschiedene. | 1 |
| In welchem Ordner auf FNSERVER001 liegen Jobs und Ergebnisse, und wie viel Platz ist dort? Entschieden: Jobs und Ereignisse bekommen eigene Ordner „_JOBS“ und „_EVENTS“ im Projektordner ../KI-Mandel/ . Die Ordner sind lokal bereits angelegt. | 3 |
| Sollen Arbeiter und Job-Server beim Start des PCs von selbst anlaufen? Entschieden: Das möge im Job-Handler bitte konfigurierbar sein. | 3 |
| Welche Bildgröße ist der Standard für neue Jobs? Entschieden: Ein abgeleitetes Bild hat dasselbe Seitenverhältnis wie sein Elternbild, voreingestellt auch dieselbe Bildgröße. Ohne Elternbild muss das Format beim Anlegen des Jobs ausgewählt werden. Wurde keines ausgewählt, muss eine Fehlermeldung abgesetzt und der Job darf nicht angelegt werden. | 4 |
| Wo läuft die Vorschau beim Einfärben? Entschieden: auf dem Server (PC) mit verkleinerten Rohdaten. Eine zweite Implementierung im Browser wird nicht gebaut. | 5b |
| Wie entstehen die Zwischenbilder im Video? Entschieden: durch Zoomen der Schlüsselbilder, nicht durch Neuberechnung. | 6 |
| Was geschieht, wenn der Pfad über die Auflösung des Ausgangsbildes hinausreicht? Entschieden: Die Pfaddefinition wird in einem Detailbild der Serie fortgesetzt. | 6 |

**Bewusst ausgeklammert:** native iPad-App, native Windows-App, Zugriff von außerhalb des Heimnetzes, Musik im Video, andere Formeln als z² + c, eine C++-Fassung des Rechenkerns. Jeder dieser Punkte braucht eine eigene Stufe mit eigener Spec, bevor daran gebaut wird.
