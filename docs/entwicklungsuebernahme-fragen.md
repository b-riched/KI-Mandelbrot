# Entwicklungsübernahme – offene Fragen an thojank

Stand: 27.11.2026 · Bearbeitungsstand: offen

Ziel: Übergabe des bestehenden Entwicklungsstands an ChatGPT. Claude (ohne Code) übernimmt V&V, Richard die finale Freigabe und Abnahme. Das Stufenkonzept bleibt maßgeblich. Bitte nur ergänzen, was nicht bereits dokumentiert ist, und möglichst auf konkrete Dateien oder Commits verweisen. Antworten können direkt unter den Fragen ergänzt werden.

## Ausgangslage (bereits ermittelt)

- Die Verzeichnisbäume von main und stufe-3-jobs enthalten identische Python-Quellen und Tests. Das neuere [Stufenkonzept](../specs/stufenkonzept.md) liegt in main.
- Stufen 0 und 1 sind dokumentiert abgenommen; 2a ist fachlich weitgehend abgenommen (B5 mit Vorbehalt), Stufe 3 teilabgenommen. Die nächste Implementierung ist laut [Abnahmebericht](abnahme-stufe-2a-und-3.md) freigegeben.
- Die Tags stufe-0, stufe-1, stufe-2a und stufe-3 existieren. stufe-3 bezeichnet ausdrücklich die Teilabnahme und zeigt auf den untersuchten Stand d0c739442226f750edeb1848104e2e1f3fccbd8a. Keine neue Abnahme wird hieraus abgeleitet.
- Der Abnahmebericht dokumentiert 547 bestandene Tests unter Windows. PR #6 dokumentiert F-01 als korrigiert und ebenfalls 547 bestandene Tests unter Linux. Ein erneuter Testlauf im Rahmen dieser Übergabe steht noch aus.
- Einrichtung und Abhängigkeiten sind in README, pyproject.toml und requirements.txt dokumentiert. Testzuordnungen stehen in den technischen Specs. Keine separate Testkonzeptdatei ist im aktuellen Verzeichnisbaum erkennbar.

## A. Fragen an thojank

### A1 – Nicht eingecheckte Artefakte und Entscheidungen (hoch)
Gibt es außerhalb des Repos noch aktuelle Spezifikationen, separate Testkonzepte, Referenzdaten, Skripte, Entwürfe, Entwicklungsnotizen oder nicht übernommene Änderungen, die für die Fortführung relevant sind? Falls ja, bitte Fundort und maßgebliche Version nennen. Gibt es insbesondere Ergebnisse aus Claude-Code-Sitzungen, die nicht in den Specs bzw. PRs dokumentiert sind?

Antwort:

### A2 – Ergänzung Stufe 3: geplant (hoch)
Das Stufenkonzept vom 22.11. fordert den Status geplant und eine explizite Freigabe nach neu. Die fachliche und technische Spec von Stufe 3 vom 18.11. kennen nur vier Zustände; die untersuchten Module server.py und warteschlange.py zeigen keine entsprechende Freigabefunktion. Gibt es bereits einen Entwurf zur nachzuziehenden Spec, zum API-Vertrag, zur Namenseindeutigkeit und zu den Tests oder eine weitere Implementierung außerhalb der beiden Branches? Falls nicht, genügt die Bestätigung, dass dies noch zu spezifizieren ist.

Antwort:

### A3 – Elternbild und Seitenverhältnis (hoch)
R19 der bisherigen fachlichen Spec lässt eine explizite Größe gelten; das neue Stufenkonzept fordert für abgeleitete Bilder gleiches Seitenverhältnis und standardmäßig dieselbe Größe. Wurde bereits entschieden, ob die Prüfung verbindlich im Job-Server/Arbeiter (Stufe 3) oder erst im MandelManager (Stufe 4) erfolgen soll? Gibt es einen dokumentierten Schnittstellenentwurf dazu?

Antwort:

### A4 – Bekannte Grenzen und technische Restarbeiten (hoch)
Die technische Spec Stufe 3 nennt ein veraltetes Lebenszeichen nach hartem Abbruch als bekannte Grenze. Sind darüber hinaus Fehler, Datenverlustrisiken, Probleme bei Netzlaufwerken, Wiederanlauf, atomarer Ablage oder numerischen Berechnungen bekannt, die nicht dokumentiert sind? Bitte auch angeben, welche bewusst auf spätere Stufen verschoben wurden.

Antwort:

### A5 – Reproduzierbarkeit (mittel)
Die Abhängigkeiten in requirements.txt sind nicht versionsfixiert. Gibt es eine erprobte Paketversionsliste für den letzten Stand (Windows/Linux), zusätzliche Installationsvoraussetzungen oder Hinweise zur Testausführung, die über README und technische Specs hinausgehen? Gibt es eine externe CI oder weitere Testläufe, deren Nachweise nicht im Repo liegen?

Antwort:

### A6 – Vorarbeiten für folgende Stufen (mittel)
Gibt es bereits konkrete, noch nicht eingecheckte Vorarbeiten für 2b (CUDA auf RTX 3080 Ti), 4 (MandelManager/TypeScript) oder 5a (Einfärber, insbesondere gebrochene Abbruchwerte und Farbzuordnung)? Bitte nur bereits bestehende Erkenntnisse oder Entwürfe nennen; keine neue Implementierung erforderlich.

Antwort:

## B. Gemeinsam mit Richard zu klären (keine alleinige Aufgabe von thojank)

- B1: Abnahmekriterien anhand der fachlichen Spec Stufe 3 abgleichen: C4 iPad, C5 Elternbild/Größe, C6 Protokoll, C7 Autostart. Der Abnahmebericht verwendet abweichende Zuordnungen. Welche konkreten Prüfungen sind tatsächlich erfolgt und welche fehlen? C3 Wiederanlauf bleibt laut Bericht offen.
- B2: Nachweise für T7 (Firewall) und T8 (Netzlaufwerk X: beim Anmelden) sowie echten Windows-Autostart zusammentragen, soweit nicht schon erfolgt. Lokale Konfiguration nur ohne Zugangsdaten dokumentieren.
- B3: Tag stufe-2a dem tatsächlich abgenommenen Stand zuordnen und den noch offenen B9-Vermerk später abgleichen. stufe-3 bleibt bis zur bestätigten Vollabnahme eine Teilabnahmereferenz. Keine Tags ohne Freigabe ändern.
- B4: Reihenfolge der nächsten Arbeiten gemeinsam festlegen: Ergänzung Stufe 3, Stufe 2b, Stufe 4 oder die gemäß Stufenkonzept unabhängig mögliche Stufe 5a. Keine Änderung des Vorgehensmodells ohne Freigabe.
- B5: Referenztestlauf am übernommenen Stand und spätere erneute Sichtprüfung B5 aus Stufe 2a nach neuer Colorierung einplanen.

## Quellen und Umfang

[README](../README.md), [Stufenkonzept](../specs/stufenkonzept.md), [fachliche Spec 2a](../specs/stufe-2a-fachlich.md), [technische Spec 2a](../specs/stufe-2a-technisch.md), [fachliche Spec 3](../specs/stufe-3-fachlich.md), [technische Spec 3](../specs/stufe-3-technisch.md), [Abnahme 0](abnahme-stufe-0.md), [Abnahme 1](abnahme-stufe-1.md), [Abnahme 2a/3](abnahme-stufe-2a-und-3.md), [PR #6](https://github.com/b-riched/KI-Mandelbrot/pull/6), [PR #8](https://github.com/b-riched/KI-Mandelbrot/pull/8), [PR #9](https://github.com/b-riched/KI-Mandelbrot/pull/9).

Dies ist ein erster Fragenkatalog auf Basis der Verzeichnisinventur, zentraler Dokumente und ausgewählter Code-/Testdateien, keine vollständige Codeprüfung oder neue Abnahme. Weitere Fragen können nach vertiefter Analyse entstehen.
