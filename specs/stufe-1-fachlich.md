# Stufe 1: Portierung – fachliche Spec

Status: freigegeben von Thorsten am 16.11.2026. Richard gibt mit der Übernahme des Pull Requests frei.
Stand: 16.11.2026
Übergeordnet: [Stufenkonzept](stufenkonzept.md)
Gegenstück: [technische Spec](stufe-1-technisch.md)

Diese Spec beschreibt, **was** Stufe 1 leistet und nach welchen Regeln. Wie es
gebaut wird, steht in der technischen Spec.

## Ziel

Richards Pipeline von 1991 läuft wieder: rechnen, Farbstufen bilden, einfärben.
Sie läuft in Python auf dem Prozessor und liefert PNG-Bilder, die den Bildern
von 1991 entsprechen. Als Beweis dienen die fünf Originaldateien in
`Org_Daten`: Die neue Fassung muss sie lesen und nachrechnen können.

## Begriffe

| Begriff | Bedeutung |
| --- | --- |
| Ausschnitt | Das Rechteck der Zahlenebene, das berechnet wird: xmin, xmax, ymin, ymax. |
| Raster | 480 × 480 Bildpunkte. In Stufe 1 fest. |
| Abbruchwert | Zahl der Rechenschritte, bis ein Punkt die Grenze überschreitet: 1 bis 1005. Der Wert 1006 heißt: Der Punkt gehört zur Menge. |
| Abbruchgrenze | Höchstzahl der Rechenschritte: 1005. In Stufe 1 fest. |
| Bereich | Eine Gruppe aufeinanderfolgender Abbruchwerte, die dieselbe Farbe bekommt. |
| Schwelle | Mindestzahl der Bildpunkte, ab der ein Bereich geschlossen wird. |
| Farbstufe | Nummer des Bereichs, in dem ein Bildpunkt liegt: 1, 2, 3 … Die Farbstufe 0 heißt: Der Punkt gehört zur Menge. |
| Palette | Tabelle, die jeder Farbstufe eine Farbe zuordnet. |
| Lauf | Eine Berechnung mit allen Ergebnissen: Abbruchwerte, Farbstufen, Bild, Beschreibung. |

## Was man nach Stufe 1 tun kann

1. **Original ansehen.** Eine der fünf `.DAT`-Dateien wird gelesen und mit
   einer der vier Paletten als PNG ausgegeben.
2. **Ausschnitt neu rechnen.** Man gibt xmin, xmax, ymin und ymax an. Es
   entstehen Abbruchwerte, Farbstufen und ein PNG.
3. **Neu einfärben, ohne neu zu rechnen.** Aus den gespeicherten
   Abbruchwerten eines Laufs entsteht mit anderer Schwelle oder anderer
   Palette ein neues Bild.
4. **Mit dem Original vergleichen.** Ein Original wird nachgerechnet. Das
   Programm meldet, wie gut Neuberechnung und Original übereinstimmen, und
   stellt beide Bilder nebeneinander.

Alle vier Abläufe werden über die Kommandozeile gestartet.

## Fachregeln

### R1 Ausschnitt und Raster

- Ein Ausschnitt besteht aus xmin, xmax, ymin, ymax. Es muss gelten
  xmin < xmax und ymin < ymax.
- Koordinaten werden als Dezimalzahl mit beliebig vielen Stellen angegeben,
  mit Punkt oder Komma. Sie werden so gespeichert, wie sie eingegeben wurden,
  und nie gerundet.
- Der Bildpunkt in Spalte x und Zeile y (beide von 1 bis 480) steht für die
  Zahl c = cx + i·cy mit
  cx = xmin + x · (xmax − xmin) / 480 und
  cy = ymin + y · (ymax − ymin) / 480.
- Folge dieser Regel, wie im Original: Der linke Rand xmin und der obere
  Rand ymin werden nicht berechnet, der rechte Rand xmax und der untere Rand
  ymax schon.
- Die Bildpunkte sind nur dann quadratisch, wenn der Ausschnitt gleich breit
  wie hoch ist. Das Programm erzwingt das nicht, wie im Original.

### R2 Berechnung der Abbruchwerte (aus MANDELDA)

- Für jeden Bildpunkt beginnt die Rechnung bei z = 0. In jedem Schritt wird
  z durch z² + c ersetzt und der Zähler um 1 erhöht.
- Die Rechnung endet, sobald der Betrag von z mindestens 2 ist, oder wenn
  der Zähler 1006 erreicht.
- Der Abbruchwert ist der Zählerstand am Ende: 1 bis 1005 für Punkte
  außerhalb der Menge, 1006 für Punkte der Menge.

### R3 Statistik: von Abbruchwerten zu Farbstufen (aus MANDELST)

Die Statistik sorgt dafür, dass die Farben gleichmäßig über das Bild verteilt
sind, statt sich am Rand der Menge zu drängen.

1. **Zählen.** Für jeden Abbruchwert von 1 bis 1005 wird gezählt, wie viele
   Bildpunkte ihn haben. Punkte der Menge (1006) zählen nicht mit.
2. **Bereiche bilden.** Die Abbruchwerte werden aufsteigend durchlaufen und
   zu Bereichen zusammengefasst. Ein Bereich wird geschlossen, sobald er
   mindestens so viele Bildpunkte enthält wie die Schwelle. Der letzte
   Bereich endet immer beim Abbruchwert 1005.
3. **Höchstzahl einhalten.** Es gibt eine Höchstzahl von Bereichen.
   Entstehen mehr, behalten die ersten Bereiche bis zur Höchstzahl ihre
   Breite. Die übrigen Abbruchwerte werden von hinten verteilt: Der letzte
   Bereich bekommt die Hälfte, der vorletzte die Hälfte vom Rest, und so
   weiter, bis nichts übrig ist. Halbe Werte werden aufgerundet.
4. **Farbstufe zuordnen.** Jeder Bildpunkt bekommt die Nummer seines
   Bereichs als Farbstufe, beginnend bei 1. Punkte der Menge bekommen 0.

Einstellbar sind zwei Größen:

| Größe | Bedeutung | Standard | Wie 1991 |
| --- | --- | --- | --- |
| Schwelle | ganze Zahl ab 0, oder „automatisch" | automatisch | von Hand gewählt, siehe Befunde |
| Höchstzahl der Bereiche | 1 bis 256 | 255 | 256 |

**Automatische Schwelle:** die kleinste Schwelle ab 1, bei der höchstens so
viele Bereiche entstehen wie die Höchstzahl. Damit werden möglichst viele
Farben genutzt, und Schritt 3 wird nicht gebraucht.

1991 fragte das Programm die Schwelle am Bildschirm ab und zeigte die
Bereiche an, bis Richard zufrieden war. Diese Abfrage entfällt. Die Schwelle
ist ein Parameter, und die Breiten aller Bereiche stehen in der Beschreibung
des Laufs.

### R4 Paletten (aus MANDPAL)

Es gibt die vier Originalpaletten mit je 256 Farben. Farbe 0 ist immer
Schwarz.

| Nr. | Verlauf |
| --- | --- |
| 0 | Schwarz über Blau und Hellblau nach Weiß. Ab Farbe 88 durchgehend Weiß. |
| 1 | Schwarz über Blau, Violett und Rot nach Gelb. Ab Farbe 208 durchgehend Gelb. |
| 2 | Schwarz über Rot und Gelb nach Hellgelb. Ab Farbe 113 durchgehend Schwarz. |
| 3 | Im Quelltext identisch mit Palette 1. |

Die Paletten werden unverändert übernommen, auch die weißen und schwarzen
Flächen in Palette 0 und 2. Neue Farbverläufe sind Stufe 5.

### R5 Einfärben und Bildlage (aus MANDELFA)

- Farbstufe 0 wird Schwarz.
- Farbstufe 1 bis 255 bekommt die Palettenfarbe mit derselben Nummer.
- Farbstufen über 255 bekommen die Palettenfarbe 255. Sie kommen nur in den
  Originaldateien vor, siehe Befunde.
- Die Bildlage ist wie 1991 am Bildschirm: Spalte 1 ist links, Zeile 1 ist
  oben. Die y-Koordinate wächst also nach unten. Gegenüber der üblichen
  mathematischen Darstellung steht das Bild auf dem Kopf.
- Das Bild ist ein PNG mit 480 × 480 Bildpunkten, ohne Achsen und ohne
  Beschriftung. Die Koordinaten stehen in der Beschreibung des Laufs.

### R6 Originaldateien lesen

Das Format der `.DAT`-Dateien steht im README. Für die Koordinaten gilt
zusätzlich diese Lesetabelle. Sie hält fest, was in der Kopfzeile steht und
mit welchen Koordinaten nachgerechnet wird.

| Datei | Faktor | Kopfzeile: xmin, xmax, ymin, ymax | Für die Nachrechnung | Grund für die Abweichung |
| --- | --- | --- | --- | --- |
| `M0.DAT` | 1000 | −2,099 / 0,600 / −1,350 / 1,350 | −2,1 / 0,6 / −1,35 / 1,35 | Die Kopfzeile schneidet Nachkommastellen ab. Aus −2,1 wurde −2,099. |
| `M01.DAT` | 1000 | −0,300 / 0,000 / −0,900 / −0,600 | wie Kopfzeile | – |
| `M1.DAT` | 1000 | −0,429 / 0,201 / −1,215 / −0,585 | wie Kopfzeile | – |
| `M11.DAT` | 1000 | −0,217 / −0,123 / −0,731 / −0,637 | −0,2175 / −0,1235 / −0,7317 / −0,6378 | Die Felder 4, 6 und 8 der Kopfzeile enthalten je eine weitere Stelle (5, 7, 8). Für xmin fehlt sie, die 5 ist durch Nachrechnen geschätzt. |
| `M12.DAT` | 10000 | −0,1443 / −0,0504 / −1,0008 / −0,9063 | wie Kopfzeile | Weitere Stellen sind verloren. |

Für andere Dateien im selben Format gibt man den Faktor von Hand an.

### R7 Vergleich mit dem Original

Der Vergleich rechnet ein Original nach und meldet zwei Kennzahlen:

- **Mengen-Übereinstimmung:** Anteil der Bildpunkte, bei denen Original und
  Neuberechnung dasselbe sagen: gehört zur Menge oder gehört nicht dazu.
- **Stufen-Übereinstimmung:** Anteil der Bildpunkte mit genau derselben
  Farbstufe. Dafür rechnet die Statistik mit der Schwelle von 1991 und mit
  256 Bereichen.

Dazu entsteht ein Vergleichsbild: links das Original, in der Mitte die
Neuberechnung, rechts die abweichenden Bildpunkte.

Eine Übereinstimmung von genau 100 % ist nicht zu erwarten. Turbo Pascal
rechnete mit einem eigenen Zahlenformat mit etwas weniger Stellen als heute
üblich. Direkt am Rand der Menge kippen dadurch einzelne Bildpunkte.

### R8 Ergebnis eines Laufs

Jeder Lauf legt einen eigenen Ordner unter `ausgabe/` an. Er enthält:

- die Abbruchwerte,
- die Farbstufen,
- das Bild als PNG,
- eine Beschreibung mit Ausschnitt (als Dezimaltext), Abbruchgrenze,
  Schwelle, Höchstzahl und Breiten der Bereiche, Palette und Herkunft
  (berechnet oder aus Originaldatei gelesen).

Ein vorhandener Lauf wird nie stillschweigend überschrieben. Der Ordner
`ausgabe/` bleibt lokal und wird nicht ins Repo eingecheckt.

## Befunde aus der Voranalyse

Die fünf Originaldateien wurden am 16.11.2026 nachgerechnet. Daraus ergibt
sich, was 1991 tatsächlich eingestellt war.

| Datei | Schwelle 1991 | Startwert des Programms | Mengen-Übereinstimmung | Stufen-Übereinstimmung |
| --- | --- | --- | --- | --- |
| `M0.DAT` | 4 | 182 | 99,95 % | 99,85 % |
| `M01.DAT` | 38 | 115 | 99,97 % | 99,23 % |
| `M1.DAT` | 14 | 196 | 99,98 % | 99,41 % |
| `M11.DAT` | etwa 52 | 46 | 99,28 % | 91,74 % |
| `M12.DAT` | 0 | 229 | 99,96 % | 86,08 % |

- **Die Schwellen sind durch Probieren ermittelt.** Es sind die Werte, mit
  denen die Neuberechnung das Original am besten trifft. Bei `M0`, `M01`,
  `M1` und `M12` ist das Ergebnis eindeutig, bei `M11` nicht.
- **Richard hat die Schwelle stark gesenkt.** Mit dem Startwert des
  Programms wären bei vier der fünf Dateien nur 46 bis 153 Bereiche
  entstanden. Mit den gewählten Werten entstanden mehr als 256, sodass alle
  Farben genutzt wurden und Schritt 3 der Statistik die obersten
  Abbruchwerte zusammenfasste. Die automatische Schwelle aus R3 liegt mit
  5, 39, 16, 54 und 1 dicht daneben.
- **Farbstufe 256 und höher.** Alle fünf Dateien enthalten die Farbstufe 256,
  `M0` und `M01` auch Werte bis 262. Eine Karte mit 256 Farben kennt aber nur
  die Farben 0 bis 255. Vermutlich wurden diese Punkte 1991 schwarz
  dargestellt. Es sind die Punkte dicht am Rand der Menge.
- **`M0` und `M01` stammen von einer älteren Programmfassung.** Der Quelltext
  kann höchstens die Farbstufe 256 erzeugen. Beide Dateien sind auch älter
  als der Quelltext von MANDELST.
- **`M11` und `M12` lassen sich nur ungenau nachrechnen.** Die Kopfzeile
  enthält zu wenige Stellen. Die Menge wird getroffen, die Farbstufen im
  Detail nicht.

## Bewusste Abweichungen vom Original

| Thema | 1991 | Stufe 1 | Grund |
| --- | --- | --- | --- |
| Schwelle | Abfrage am Bildschirm | Parameter, Standard automatisch | Läuft ohne Rückfrage, Voraussetzung für Jobs in Stufe 3 |
| Höchstzahl der Bereiche | 256 | 255, auf Wunsch 256 | Farbstufe 256 hat keine eigene Farbe |
| Farbstufen über 255 | vermutlich Schwarz | Palettenfarbe 255 | Punkte außerhalb der Menge sollen nicht wie die Menge aussehen |
| Koordinaten | 3 bis 4 Nachkommastellen in der Kopfzeile | Dezimaltext ohne Grenze | Grundentscheidung im Stufenkonzept |
| Anzeige | Bildschirm mit Achsen und Koordinaten | PNG-Datei ohne Beschriftung | Standardformat, Anzeige kommt in Stufe 4 |
| Ablage | eine Datei pro Schritt, feste Pfade | ein Ordner pro Lauf | Nichts wird überschrieben |
| Zahlenformat | Turbo-Pascal-Zahlen | heutige Standard-Gleitkommazahlen | Einzelne Randpunkte weichen ab, siehe R7 |

## Nicht in dieser Stufe

- Grafikkarte, andere Bildgrößen, andere Abbruchgrenze (Stufe 2).
- Neue Farbverläufe, gebrochene Abbruchwerte, Höhenlinien (Stufe 5).
- Jobs, Server, Web-App, jede Art von Bedienoberfläche (Stufen 3 und 4).
- Ausschnittwahl mit der Maus. MANDMAUS wird nicht portiert.
- Die eigene Formel aus MANDELMO.
- Schreiben von `.DAT`-Dateien im alten Format.
- Rekonstruktion der verlorenen Koordinatenstellen von `M11` und `M12`.
- Byte-genaue Nachbildung der Turbo-Pascal-Zahlen.

## Entscheidungen

Thorsten hat am 16.11.2026 alle sechs Vorschläge übernommen. So ist Stufe 1
gebaut. Richard kann im Pull Request widersprechen, dann wird nachgebaut.

| Nr. | Frage | Entschieden wie vorgeschlagen |
| --- | --- | --- |
| F1 | Welche Schwelle gilt, wenn keine angegeben ist? | Automatisch nach R3. Das trifft Richards Vorgehen von 1991 und braucht keine Rückfrage. |
| F2 | Höchstens 255 oder 256 Bereiche für neue Bilder? | 255. Dann hat jede Farbstufe eine eigene Farbe. |
| F3 | Wie werden die Farbstufen über 255 in den Originalen dargestellt? | Mit Palettenfarbe 255. Alternative: Schwarz, wie vermutlich 1991. |
| F4 | Bleibt das Bild auf dem Kopf wie 1991? | Ja, in Stufe 1. Stufe 2 legt mit Mittelpunkt und Bildbreite die Lage für neue Bilder fest. |
| F5 | Stimmen die Koordinaten der Lesetabelle? Wurde `M0` mit xmin = −2,1 gerechnet? | So übernehmen, wenn Richard nichts anderes weiß. |
| F6 | War Palette 3 als Kopie von Palette 1 gedacht? | Unverändert übernehmen. |

## Abnahme

- [ ] **A1** Alle fünf Originaldateien werden gelesen und mit jeder der vier
      Paletten als PNG ausgegeben. Das sind 20 Bilder.
- [ ] **A2** Mengen-Übereinstimmung beim Nachrechnen: mindestens 99,9 % bei
      `M0`, `M01`, `M1` und `M12`, mindestens 99,0 % bei `M11`.
- [ ] **A3** Stufen-Übereinstimmung mit der Schwelle von 1991 und
      256 Bereichen: mindestens 99,5 % bei `M0`, mindestens 99,0 % bei `M01`
      und `M1`. Für `M11` und `M12` wird der Wert ausgewiesen, eine Grenze
      gibt es nicht.
- [ ] **A4** Ein eigener Ausschnitt wird über die Kommandozeile gerechnet.
      Der Lauf-Ordner ist vollständig, und die Koordinaten stehen in der
      Beschreibung genau so, wie sie eingegeben wurden.
- [ ] **A5** Ein vorhandener Lauf wird mit anderer Palette und anderer
      Schwelle neu eingefärbt, ohne dass neu gerechnet wird.
- [ ] **A6** Richard sieht sich für jede der fünf Dateien das Vergleichsbild
      an und nimmt es ab.
- [ ] **A7** Alle Tests laufen mit einem einzigen Befehl.
- [ ] **A8** Der Stand trägt die Marke `stufe-1`.

## Ergebnis für die nächste Stufe

Stufe 2 kann sich darauf verlassen, dass es eine geprüfte Rechnung auf dem
Prozessor gibt, gegen die sich die Grafikkarte vergleichen lässt, und dass
Statistik, Paletten und Ablage unabhängig vom Rechenkern funktionieren.
