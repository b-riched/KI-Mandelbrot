# KI-Mandelbrot: Stufenkonzept

Stand: 12.11.2026 · Thorsten

## Zweck und Arbeitsweise

Jede Stufe wird erst spezifiziert, dann gebaut, dann abgenommen. Die nächste Stufe beginnt erst nach der Abnahme der vorigen.

Dieses Dokument ist das Dach über allen Stufen. Es legt fest, was jede Stufe liefert und woran wir erkennen, dass sie fertig ist. Die Detail-Spec einer Stufe entsteht erst, wenn sie an der Reihe ist.

Ablauf pro Stufe:

1. **Spec schreiben.** Eine Datei `specs/stufe-N.md` im Repo mit Ziel, Umfang, Nicht-Umfang, Schnittstellen und Abnahmekriterien.
2. **Spec freigeben.** Richard und Thorsten lesen sie und sagen ja oder ändern sie.
3. **Bauen.** Claude baut genau das, was in der Spec steht, nicht mehr.
4. **Abnehmen.** Die Abnahmekriterien werden einzeln geprüft. Der abgenommene Stand bekommt im Repo die Marke `stufe-N`.
5. **Funde parken.** Was beim Bauen auffällt und nicht in der Spec steht, kommt in die Spec einer späteren Stufe oder in die offenen Punkte, nicht in den Code.

Der Abschnitt „Nicht in dieser Stufe" ist bei jeder Stufe genauso verbindlich wie der Umfang. Er ist der Schutz davor, im Wald zu landen.

## Festgelegte Grundentscheidungen

Diese Punkte sind entschieden und gelten für alle Stufen. Wer einen davon ändern will, ändert zuerst dieses Dokument.

| Thema | Festlegung |
| --- | --- |
| Rechenkern | Python mit Numba-CUDA. Variante: CuPy mit der Rechenschleife in CUDA-C. |
| Grafikkarte | RTX 3080 Ti, eingebaut. Die RTX 4070 Ti Super bleibt als Alternative. |
| Job-Server | Python mit FastAPI, läuft auf dem Windows-PC. |
| Server FNSERVER001 | Nur Dateiablage für Jobs und Ergebnisse. |
| Bedienung | Web-App in TypeScript, im Browser auf PC und iPad. |
| Netz | Nur Heimnetz. Ein VPN richtet Richard bei Bedarf selbst ein. |
| Zoomtiefe Stufen 1 bis 6 | Bis etwa 10⁻¹² Bildbreite. Tiefer erst in Stufe 7. |
| Ausgabeformate | Bilder als PNG, Videos als MP4, Metadaten als JSON. |
| Koordinaten | Als Dezimaltext mit beliebig vielen Stellen, nie als gerundete Zahl. |
| Originale | `Org_Daten` und `Org_Sourcen` bleiben unverändert im Repo. |
| Repo | [b-riched/KI-Mandelbrot](https://github.com/b-riched/KI-Mandelbrot) |

## Stufenübersicht

Acht Stufen, jede mit einem vorzeigbaren Ergebnis. Nach Stufe 4 ist Richards Kreislauf von 1991 wieder geschlossen: rechnen, ansehen, Ausschnitt wählen, neu rechnen.

| Stufe | Name | Ergebnis | Baut auf |
| --- | --- | --- | --- |
| 0 | Fundament | Repo-Struktur steht, Originale sind geschützt und dokumentiert | – |
| 1 | Portierung | Richards Pipeline läuft in Python und erzeugt PNG wie 1991 | 0 |
| 2 | GPU und Bildgrößen | Berechnung auf der Grafikkarte, Bildgröße und Abbruchgrenze frei wählbar | 1 |
| 3 | Jobs und Server | Jobs liegen als Dateien auf dem Server, der PC arbeitet sie ab | 2 |
| 4 | Web-App | Bilder ansehen und Ausschnitt wählen auf PC und iPad | 3 |
| 5 | Farben und Relief | 24-Bit-Farbverläufe, Höhenlinien, Relief | 2 |
| 6 | Videos | Zoomfahrt hinein oder heraus als MP4 | 3 und 5 |
| 7 | Tiefe Zooms | Bildbreiten kleiner als 10⁻¹² | 2 |

Stufe 5 braucht nur die Rohdaten aus Stufe 2. Sie kann deshalb vor Stufe 3 und 4 gezogen werden, wenn Richard früh schöne Bilder sehen will.

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
- **Paletten** (aus MANDPAL): die vier Originalpaletten.
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

## Stufe 2: GPU und Bildgrößen

**Ziel:** Der Rechenkern läuft auf der RTX 3080 Ti, und Bildgröße und Abbruchgrenze sind frei wählbar.

**Umfang**

- Rechenschleife mit Numba-CUDA in doppelter Genauigkeit.
- Ein Ausschnitt wird durch Mittelpunkt und Bildbreite beschrieben. Die Bildhöhe ergibt sich aus dem Seitenverhältnis, die Bildpunkte bleiben quadratisch.
- Bildgrößen 1280 × 720, 1920 × 1080, 2560 × 1440 und 2360 × 1640, dazu jede frei gewählte Größe.
- Abbruchgrenze als Parameter.
- Zusätzlich zu den ganzen Abbruchwerten werden gebrochene Abbruchwerte gespeichert. Sie sind die Grundlage für stufenlose Farben in Stufe 5.
- Derselbe Aufruf rechnet auf dem Prozessor, wenn keine Grafikkarte da ist.
- Warnung, wenn die Bildbreite unter 10⁻¹² liegt.

**Nicht in dieser Stufe:** Störungsrechnung, Jobs, Farben. Die CuPy-Variante wird nur gebaut, wenn Numba an eine Grenze stößt.

**Abnahme**

- [ ] Grafikkarte und Prozessor liefern für denselben Ausschnitt in mindestens 99,9 % der Punkte denselben ganzen Abbruchwert.
- [ ] Ein Bild mit 10⁻¹² Bildbreite in 2560 × 1440 zeigt keine Klötzchen.
- [ ] Die Rechenzeiten für die vier Bildgrößen sind auf Richards PC gemessen und in der Spec eingetragen.
- [ ] Die Installation auf Richards PC ist als Schrittfolge im README beschrieben und einmal von ihm durchgespielt.

## Stufe 3: Jobs und Server

**Ziel:** Jede Berechnung wird über eine Job-Datei gesteuert, und der PC arbeitet die Warteschlange selbständig ab.

**Umfang**

- **Job-Format** als JSON: Name, Mittelpunkt und Bildbreite als Dezimaltext, Bildgröße, Abbruchgrenze, Palette, Elternbild und Serie.
- **Ordner auf dem Server:** `jobs/neu`, `jobs/laeuft`, `jobs/fertig`, `jobs/fehler` und `ergebnisse/<Jobname>/` mit Rohdaten, PNG und Metadaten.
- **Arbeiter** auf dem PC: holt den ältesten Job aus `jobs/neu`, rechnet, färbt ein, legt das Ergebnis ab.
- **Job-Server** auf dem PC: Job anlegen, Jobs mit Status auflisten, Bilder und Metadaten ausliefern.

**Nicht in dieser Stufe:** Bedienoberfläche, Anmeldung, Zugriff von außerhalb des Heimnetzes, mehrere Arbeiter gleichzeitig.

**Abnahme**

- [ ] Eine von Hand in `jobs/neu` gelegte Job-Datei wird gerechnet, und das Ergebnis liegt im Ergebnisordner.
- [ ] Ein fehlerhafter Job landet mit lesbarer Meldung in `jobs/fehler`, und die Warteschlange läuft weiter.
- [ ] Nach einem Neustart des PCs mitten in einem Job wird dieser Job neu gerechnet und geht nicht verloren.
- [ ] Vom iPad aus lässt sich über die Adresse des PCs im Heimnetz ein Job anlegen und sein Status abfragen.

## Stufe 4: Web-App

**Ziel:** Richard kann am PC und am iPad Bilder ansehen, den nächsten Ausschnitt wählen und den Job abschicken.

**Umfang**

- **Galerie** aller fertigen Bilder, neueste zuerst.
- **Bildansicht** mit Vergrößern und Verschieben.
- **Ausschnittwahl** mit Maus oder Finger: ein Rahmen im festen Seitenverhältnis der gewählten Bildgröße.
- **Job-Formular** mit Bildgröße, Abbruchgrenze und Palette.
- **Job-Liste** mit Status, die sich selbst aktualisiert.
- **Zoom-Kette:** Jedes Bild kennt sein Elternbild. Das ist die Grundlage für die Videos in Stufe 6.
- Auf dem iPad lässt sich die Web-App auf den Home-Bildschirm legen.

**Nicht in dieser Stufe:** Berechnung im Browser, Anmeldung, native iPad-App, Zugriff von außen, Videos.

**Abnahme**

- [ ] Am iPad: Bild öffnen, Ausschnitt wählen, Job abschicken, das fertige Bild erscheint in der Galerie.
- [ ] Derselbe Ablauf am PC mit der Maus.
- [ ] Das neue Bild zeigt genau den gewählten Rahmen.
- [ ] Von jedem Bild führt ein Klick zum Elternbild.

## Stufe 5: Farben und Relief

**Ziel:** Der Einfärber erzeugt aus gespeicherten Rohdaten Bilder mit stufenlosen Farbverläufen, Höhenlinien und Relief, ohne neu zu rechnen.

**Umfang**

- Richards Statistik-Verfahren auf den gebrochenen Abbruchwerten, mit 8 Bit pro Farbkanal.
- Farbverläufe als kleine Textdateien mit Stützfarben. Richards vier Paletten bleiben als Verläufe erhalten.
- Höhenlinien mit einstellbarem Abstand.
- Relief-Schattierung mit einstellbarer Lichtrichtung.
- Ein vorhandenes Ergebnis lässt sich neu einfärben, als eigener Job-Typ.

**Nicht in dieser Stufe:** Ein Farb-Editor mit Oberfläche. Verläufe werden als Datei angelegt.

**Abnahme**

- [ ] Ein vorhandenes Ergebnis wird neu eingefärbt, ohne dass der Rechenkern läuft.
- [ ] In ruhigen Bildbereichen sind keine Farbstufen zu sehen.
- [ ] Höhenlinien und Relief lassen sich einzeln ein- und ausschalten.
- [ ] Richard hat mindestens drei Verläufe als Standard ausgewählt.

## Stufe 6: Videos

**Ziel:** Aus einem Zielpunkt entsteht eine Zoomfahrt als MP4, wahlweise hinein (Descend) oder heraus (Ascend).

**Umfang**

- **Serien-Job:** Mittelpunkt, Startbreite und Endbreite. Daraus entstehen Schlüsselbilder, jedes mit der halben Bildbreite des vorigen. Von der Gesamtansicht bis 10⁻¹² sind das etwa 42 Schlüsselbilder.
- **Zwischenbilder** entstehen durch Vergrößern und Überblenden benachbarter Schlüsselbilder, nicht durch Neuberechnung.
- **Zeitkurve:** Die Fahrt beginnt langsam, wird schneller und endet langsam.
- **Einheitliche Farbzuordnung** über die ganze Fahrt, damit die Farben nicht flackern.
- **Ausgabe** als MP4 über ffmpeg, in 1920 × 1080.
- Die Ascend-Fahrt nutzt dieselben Schlüsselbilder in umgekehrter Reihenfolge.

**Nicht in dieser Stufe:** Musik (die kommt im Videoschnittprogramm dazu), Schwenks und Drehungen der Kamera, Farbwechsel während der Fahrt.

**Abnahme**

- [ ] Eine Fahrt von der Gesamtansicht bis 10⁻¹² liegt als MP4 vor und spielt auf PC und iPad.
- [ ] An den Übergängen zwischen Schlüsselbildern ist kein Sprung zu sehen.
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
| Gibt es die Units `MOUSE` und `MOUSEWIN` und die Rohdateien `mandelN.dat` noch? Entschieden: MOUSE und MOUSEWIN sind Units aus der Turbo-Pascal 5.5 Bibiliothek. Diese stehen nicht mehr zur Verfügung. | 1 |
| In welchem Ordner auf FNSERVER001 liegen Jobs und Ergebnisse, und wie viel Platz ist dort? Entschieden: Jobs und Ereignisse bekommen eingene Ordner „_JOBS“ und „_EVENTS“ im Projektordner ../KI-Mandel/ . Die Ordner sind lokal bereits angelegt. | 3 |
| Sollen Arbeiter und Job-Server beim Start des PCs von selbst anlaufen? Entschieden: Das möge im Job-Handler bitte konfigurierbar sein. | 3 |
| Welche Bildgröße ist der Standard für neue Jobs? Entschieden: Wenn das Bild ein Elternbild hat, dann das Format des Elternbildes. Ansonsten muss das Format beim Anlegen des Jobs ausgewählt werden. Wurde keines ausgewählt, muss eine Fehlermeldung abgesetzt und der Job darf nicht angelegt werden. | 4 |

**Bewusst ausgeklammert:** native iPad-App, Zugriff von außerhalb des Heimnetzes, Musik im Video, andere Formeln als z² + c, eine C++-Fassung des Rechenkerns. Jeder dieser Punkte braucht eine eigene Stufe mit eigener Spec, bevor daran gebaut wird.
