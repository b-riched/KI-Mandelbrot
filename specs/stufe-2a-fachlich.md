# Stufe 2a: Bildgrößen und freier Ausschnitt – fachliche Spec

Status: freigegeben von Thorsten am 16.11.2026. Richard gibt mit der Übernahme des Pull Requests frei.
Stand: 16.11.2026
Übergeordnet: [Stufenkonzept](stufenkonzept.md)
Gegenstück: [technische Spec](stufe-2a-technisch.md)
Baut auf: [Stufe 1](stufe-1-fachlich.md)

Stufe 2 des Stufenkonzepts ist geteilt. Stufe 2a enthält alles, was ohne
Grafikkarte geht. Stufe 2b bringt dieselbe Rechnung auf die Grafikkarte.

## Ziel

Bilder lassen sich in frei wählbarer Größe rechnen, mit wählbarer
Abbruchgrenze und mit einem Ausschnitt, der durch Mittelpunkt und Bildbreite
beschrieben ist. Gerechnet wird weiter auf dem Prozessor. Damit steht fest,
wie ein Bild beschrieben wird. Darauf bauen die Jobs in Stufe 3 auf.

## Neue Begriffe

| Begriff | Bedeutung |
| --- | --- |
| Bildgröße | Breite und Höhe des Bildes in Bildpunkten, zum Beispiel 1920 × 1080. |
| Mittelpunkt | Die Zahl der Zahlenebene, die genau in der Bildmitte liegt. |
| Bildbreite | Breite des Ausschnitts in der Zahlenebene, vom linken zum rechten Bildrand. |
| Punktabstand | Abstand zweier benachbarter Bildpunkte in der Zahlenebene: Bildbreite geteilt durch die Breite in Bildpunkten. |
| Gebrochener Abbruchwert | Ein Abbruchwert mit Nachkommastellen. Er ändert sich von Bildpunkt zu Bildpunkt stufenlos. |

Die Begriffe aus Stufe 1 gelten weiter.

## Was man nach Stufe 2a tun kann

1. **Ein Bild in HD, Full HD, WQHD, iPad-Größe oder jeder anderen Größe
   rechnen.** Man gibt Mittelpunkt, Bildbreite und Bildgröße an.
2. **Die Abbruchgrenze wählen.** Für tiefe Ausschnitte braucht man mehr als
   1005 Schritte.
3. **Alles aus Stufe 1 weiter benutzen.** Originale lesen, vergleichen und
   neu einfärben funktionieren unverändert.

## Fachregeln

Die Regeln R1 bis R8 aus Stufe 1 gelten weiter. Neu sind R9 bis R16.

### R9 Bildgröße

- Eine Bildgröße ist Breite mal Höhe in Bildpunkten. Jede Seite hat
  mindestens 16 und höchstens 10.000 Bildpunkte.
- Vier Größen haben Namen:

| Name | Bildpunkte |
| --- | --- |
| `hd` | 1280 × 720 |
| `fullhd` | 1920 × 1080 |
| `wqhd` | 2560 × 1440 |
| `ipad` | 2360 × 1640 |

- Jede andere Größe wird als `BREITExHÖHE` angegeben, zum Beispiel
  `800x600`.
- Es gibt keinen Standard. Die Bildgröße muss angegeben werden. Das
  entspricht Richards Entscheidung im Stufenkonzept.

### R10 Ausschnitt durch Mittelpunkt und Bildbreite

- Ein Bild wird durch Mittelpunkt (zwei Dezimalzahlen), Bildbreite (eine
  Dezimalzahl größer als 0) und Bildgröße beschrieben.
- Der Punktabstand ist Bildbreite geteilt durch die Breite in Bildpunkten.
  Er gilt waagerecht und senkrecht. Die Bildpunkte sind also immer
  quadratisch, und die Höhe des Ausschnitts ergibt sich aus der Bildgröße.
- Der Mittelpunkt liegt genau in der Bildmitte. Der Bildpunkt in Spalte i
  und Zeile j (ab 1 gezählt) eines Bildes mit B × H Bildpunkten und
  Punktabstand a steht für
  cx = Mittelpunkt-x + (i − (B + 1) / 2) · a und
  cy = Mittelpunkt-y − (j − (H + 1) / 2) · a.
- Mittelpunkt und Bildbreite werden als Dezimaltext gespeichert, so wie sie
  eingegeben wurden.

### R11 Bildlage

- Bilder nach R10 stehen aufrecht wie in der Mathematik üblich: Die
  y-Koordinate wächst nach oben.
- Bilder nach R1 (mit xmin, xmax, ymin, ymax) und die Originale bleiben, wie
  sie 1991 waren. Das hält die Vergleiche aus Stufe 1 gültig.

### R12 Abbruchgrenze

- Die Abbruchgrenze ist eine ganze Zahl von 10 bis 1.000.000. Ohne Angabe
  gilt 1005, wie 1991.
- Die Rechenregel R2 bleibt gleich. Punkte der Menge haben den Abbruchwert
  Abbruchgrenze plus 1.

### R13 Gebrochene Abbruchwerte

- Zu jedem Bild nach R10 werden neben den ganzen Abbruchwerten auch
  gebrochene gespeichert. Bilder nach R1 (wie 1991) bleiben wie in Stufe 1.
- Dafür wird nach dem Abbruch noch wenige Schritte weitergerechnet, bis der
  Betrag von z groß ist. Aus Schrittzahl und Betrag ergibt sich ein Wert,
  der zwischen benachbarten Bildpunkten stufenlos verläuft.
- Für Punkte der Menge hat der gebrochene Wert keine Bedeutung. Ob ein
  Punkt zur Menge gehört, sagt immer der ganze Abbruchwert.
- In Stufe 2a werden die gebrochenen Werte nur gespeichert. Statistik und
  Farben arbeiten weiter mit den ganzen Werten. Benutzt werden die
  gebrochenen Werte in Stufe 5.

### R14 Statistik bei anderer Abbruchgrenze

Die Statistik R3 gilt unverändert. An die Stelle von 1005 tritt die
Abbruchgrenze des Bildes. Die automatische Schwelle ist definiert wie in
Stufe 1.

### R15 Grenze der Rechengenauigkeit

Der Prozessor unterscheidet Zahlen nur bis zu einer festen Feinheit. Wird
der Punktabstand kleiner, bekommen benachbarte Bildpunkte dieselbe
Koordinate, und es entstehen Klötzchen.

- **Warnung**, wenn die Bildbreite unter 10⁻¹² liegt oder wenn der
  Punktabstand weniger als das Vierfache der Feinheit beträgt. Das Bild wird
  gerechnet, die Punkte liegen aber nicht mehr gleichmäßig.
- **Fehler**, wenn zwei benachbarte Spalten oder Zeilen dieselbe Koordinate
  bekämen. Das Bild wird nicht gerechnet.

Gemessen: Bei 2560 Bildpunkten Breite und 10⁻¹² Bildbreite sind alle Spalten
verschieden. Bei 10⁻¹³ fallen je nach Lage des Mittelpunkts schon Spalten
zusammen. Tiefer geht es erst mit Stufe 7.

### R16 Beschreibung des Laufs

Die Beschreibung eines Laufs enthält zusätzlich Mittelpunkt, Bildbreite,
Bildgröße und Bildlage. Läufe aus Stufe 1 bleiben lesbar.

## Kommandozeile

Der Befehl `berechne` kennt zwei Formen. Man benutzt genau eine davon.

| Form | Angaben | Ergebnis |
| --- | --- | --- |
| wie 1991 | xmin, xmax, ymin, ymax | 480 × 480, Lage wie 1991 |
| neu | Mittelpunkt, Bildbreite, Bildgröße | gewählte Größe, aufrecht |

In beiden Formen lässt sich die Abbruchgrenze angeben. Die Befehle
`original`, `faerbe` und `vergleiche` bleiben, wie sie sind.

## Messwerte aus der Voranalyse

Gerechnet am 16.11.2026 mit einem Versuchsaufbau auf dem Prozessor, Ansicht
der ganzen Menge, Abbruchgrenze 1005:

| Bildgröße | Rechenzeit |
| --- | --- |
| 480 × 480 | 0,3 Sekunden (Stufe 1: 2,4 Sekunden) |
| 1280 × 720 | 1,1 Sekunden |
| 2560 × 1440 | 4,7 Sekunden |

Die Zeiten des fertigen Programms stehen in der technischen Spec.

Der neue Rechenweg liefert für die Ausschnitte aus Stufe 1 genau dieselben
Abbruchwerte wie Stufe 1.

## Nicht in dieser Stufe

- Rechnen auf der Grafikkarte (Stufe 2b).
- Jobs und Server (Stufe 3).
- Farben aus gebrochenen Abbruchwerten, Höhenlinien, Relief (Stufe 5).
- Bildbreiten, bei denen R15 einen Fehler meldet (Stufe 7).
- Ausschnittwahl mit Maus oder Finger (Stufe 4).
- Gedrehte oder verzerrte Ausschnitte.
- Umrechnen alter Läufe in die neue Form.

## Entscheidungen

Thorsten hat am 16.11.2026 alle fünf Vorschläge übernommen. So ist Stufe 2a
gebaut. Richard hat sie am 18.11.2026 nach seinen Tests freigegeben. Offen
sind noch B5 (das tiefe Bild ansehen), B8 (Rechenzeiten auf Richards PC)
und B9 (Marke).

| Nr. | Frage | Entschieden wie vorgeschlagen |
| --- | --- | --- |
| G1 | Stehen neue Bilder aufrecht, anders als 1991? | Ja. Das ist die übliche Darstellung, und Web-App und Videos brauchen eine feste Lage. |
| G2 | Reichen die vier benannten Größen? | Ja. Jede andere Größe geht als `BREITExHÖHE`. |
| G3 | Welche Abbruchgrenze gilt ohne Angabe? | 1005, wie 1991. |
| G4 | Passen die Grenzen: Seiten bis 10.000 Bildpunkte, Abbruchgrenze bis 1.000.000? | Ja. Sie schützen nur vor Tippfehlern. |
| G5 | Reicht es, die gebrochenen Abbruchwerte in 2a nur zu speichern? | Ja. Farben daraus sind Stufe 5. |

## Abnahme

- [ ] **B1** Je ein Bild in `hd`, `fullhd`, `wqhd` und `ipad` und eines in
      einer frei gewählten Größe ist gerechnet. Jedes PNG hat genau die
      verlangte Größe.
- [ ] **B2** Der Mittelpunkt liegt in der Bildmitte, die Bildpunkte sind
      quadratisch, und das Bild steht aufrecht.
- [ ] **B3** Alle Tests aus Stufe 1 laufen unverändert durch. Die
      Übereinstimmung mit den fünf Originalen ist dieselbe wie in Stufe 1.
- [ ] **B4** Ein Bild mit Abbruchgrenze 5000 ist gerechnet. Die Breiten der
      Bereiche ergeben zusammen 5000.
- [ ] **B5** Ein Bild mit 10⁻¹² Bildbreite in 2560 × 1440 ist gerechnet.
      Richard sieht es an: keine Klötzchen.
- [ ] **B6** Warnung und Fehler nach R15 erscheinen an den richtigen
      Stellen.
- [ ] **B7** Zu jedem neuen Lauf gibt es gebrochene Abbruchwerte.
- [ ] **B8** Die Rechenzeiten für die vier benannten Größen sind gemessen
      und in der technischen Spec eingetragen.
- [ ] **B9** Der Stand trägt die Marke `stufe-2a`.

## Ergebnis für die nächsten Stufen

- **Stufe 3** kann einen Job mit Mittelpunkt, Bildbreite, Bildgröße und
  Abbruchgrenze beschreiben.
- **Stufe 2b** hat einen geprüften Rechenweg auf dem Prozessor, gegen den
  sich die Grafikkarte Bildpunkt für Bildpunkt vergleichen lässt.
- **Stufe 5** findet zu jedem Lauf gebrochene Abbruchwerte vor.
