# Entwicklungsübernahme – offene Fragen an thojank

Stand: 28.11.2026 · Bearbeitungsstand: A1 bis A6 beantwortet von thojank am 28.11.2026, Teil B offen

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

Antwort (thojank, 28.11.2026): Außerhalb des Repos liegt nur eines, das für die Fortführung zählt: der Entwurf der Spec für Stufe 3 Teil C (Stand `geplant`, siehe A2). Er kommt als eigener Branch ins Repo.

Sonst gibt es nichts Maßgebliches außerhalb. Alle Ergebnisse aus den Claude-Sitzungen stehen in den Specs, in den Abschnitten „Präzisierungen beim Bauen von Teil A/B" der technischen Spec Stufe 3, in den Commits und in den Pull Requests. Zwei Dinge liegen außerhalb, enthalten aber keine Entscheidungen, die nicht schon im Repo stehen:

- die Beschreibung von Thorstens Arbeitsumgebung, geschrieben für Richard,
- das Whiteboard mit Plan und Architektur, das Richard hat.

Getrennte Testkonzepte, Referenzdaten oder Skripte gibt es nicht. Die Tests und ihre Zuordnung zu den Kriterien stehen in den technischen Specs.

### A2 – Ergänzung Stufe 3: geplant (hoch)
Das Stufenkonzept vom 22.11. fordert den Status geplant und eine explizite Freigabe nach neu. Die fachliche und technische Spec von Stufe 3 vom 18.11. kennen nur vier Zustände; die untersuchten Module server.py und warteschlange.py zeigen keine entsprechende Freigabefunktion. Gibt es bereits einen Entwurf zur nachzuziehenden Spec, zum API-Vertrag, zur Namenseindeutigkeit und zu den Tests oder eine weitere Implementierung außerhalb der beiden Branches? Falls nicht, genügt die Bestätigung, dass dies noch zu spezifizieren ist.

Antwort (thojank, 28.11.2026): Ja, ein vollständiger Entwurf liegt vor (23.11.2026), bisher nicht eingecheckt. Er ergänzt beide Specs von Stufe 3:

- fachlich: Regel R27 „Geplante Jobs", Kriterium C10, Anpassungen an R17, R20, R24, R25 und offene Entscheidungen H7 bis H9,
- technisch: Abschnitt „Teil C" mit fünftem Ordner, neuem Feld `freigegeben`, Aufruf `POST /api/jobs/{name}/freigeben`, Reihenfolge nach Freigabezeitpunkt, Protokoll und Tests.

Namenseindeutigkeit: Ein geplanter Job belegt seinen Namen wie jeder andere, geprüft über alle fünf Ordner und `_ERGEBNISSE`. Eine Implementierung außerhalb der Branches gibt es nicht. Der Entwurf kommt als Branch `stufe-3-teil-c` mit Pull Request, dort werden H7 bis H9 entschieden.

### A3 – Elternbild und Seitenverhältnis (hoch)
R19 der bisherigen fachlichen Spec lässt eine explizite Größe gelten; das neue Stufenkonzept fordert für abgeleitete Bilder gleiches Seitenverhältnis und standardmäßig dieselbe Größe. Wurde bereits entschieden, ob die Prüfung verbindlich im Job-Server/Arbeiter (Stufe 3) oder erst im MandelManager (Stufe 4) erfolgen soll? Gibt es einen dokumentierten Schnittstellenentwurf dazu?

Antwort (thojank, 28.11.2026): Nicht entschieden, und es gibt keinen Schnittstellenentwurf über R18 und R19 hinaus.

Stand heute: R19 erlaubt bei einem Job mit Elternbild eine abweichende Bildgröße, auch mit anderem Seitenverhältnis. Das Stufenkonzept fordert „immer dasselbe Seitenverhältnis", aber im Abschnitt zu Stufe 4 (MandelManager).

Vorschlag: Die Frage kommt als H10 in den Entwurf zu Teil C. Empfehlung dort: Job-Server und Arbeiter prüfen verbindlich, weil Jobs auch als Datei und über die Testseite entstehen und Stufe 6 sich auf gleiche Seitenverhältnisse in einer Serie verlässt. Der MandelManager stellt in Stufe 4 nur die Voreinstellung.

### A4 – Bekannte Grenzen und technische Restarbeiten (hoch)
Die technische Spec Stufe 3 nennt ein veraltetes Lebenszeichen nach hartem Abbruch als bekannte Grenze. Sind darüber hinaus Fehler, Datenverlustrisiken, Probleme bei Netzlaufwerken, Wiederanlauf, atomarer Ablage oder numerischen Berechnungen bekannt, die nicht dokumentiert sind? Bitte auch angeben, welche bewusst auf spätere Stufen verschoben wurden.

Antwort (thojank, 28.11.2026): Darüber hinaus sind keine Fehler oder Datenverlustrisiken bekannt. Bekannt und dokumentiert, aber noch nicht auf Richards PC geprüft:

- **Lebenszeichen:** Nach hartem Abbruch meldet der Job-Server den Arbeiter weiter als aktiv (technische Spec Stufe 3).
- **Testseite:** `/docs` lädt ihre Bedienelemente aus dem Internet. Das Gerät braucht also eine Internetverbindung, die Aufrufe unter `/api` nicht (Präzisierung 10, Teil B).
- **Windows:** Firewall beim ersten Start (T7) und verbundenes Laufwerk X: beim Autostart (T8) sind offen. Ebenso das Beenden mit Strg+C bei `start` unter Windows. Gebaut und getestet wurde nur unter Linux.
- **Netzlaufwerk:** Der Stand eines Jobs wechselt durch Umbenennen innerhalb von `_JOBS` (`os.replace`), Dateien entstehen über `.teil` und Umbenennen. Auf einem Netzlaufwerk ist das nicht unter Last geprüft.
- **Numerik:** Bis etwa 10⁻¹² Bildbreite gilt Stufe 1/2a („Weg 1"), tiefer erst Stufe 7. Darunter warnt das Programm nach R15.

Bewusst verschoben (siehe „Nicht in dieser Stufe"): Jobs abbrechen oder löschen, mehrere Arbeiter, Windows-Dienst statt Autostart, Zugriff der Web-App von anderer Adresse (CORS, Stufe 4), Aufräumen alter Jobs, neue Farbzuordnung (Stufe 5a, betrifft den Vorbehalt bei B5).

### A5 – Reproduzierbarkeit (mittel)
Die Abhängigkeiten in requirements.txt sind nicht versionsfixiert. Gibt es eine erprobte Paketversionsliste für den letzten Stand (Windows/Linux), zusätzliche Installationsvoraussetzungen oder Hinweise zur Testausführung, die über README und technische Specs hinausgehen? Gibt es eine externe CI oder weitere Testläufe, deren Nachweise nicht im Repo liegen?

Antwort (thojank, 28.11.2026): Es gibt keine CI und keine Testläufe außerhalb des Repos. Gebaut und getestet wurde in einer Linux-Umgebung mit Python 3.13. Stand 18.11.2026 liefen dort alle 732 Tests durch, mit Job-Server.

Erprobte Versionen: fastapi 0.165.0, starlette 1.7.0, uvicorn 0.54.0, pydantic 2.13.5, httpx 0.28.1, numpy 2.5.3, pillow 12.3.0, pytest 9.1.1.

Der Windows-Lauf im Abnahmebericht (547 Tests, Python 3.14) stammt vom Stand vor dem Job-Server. Nach `pip install -r requirements.txt` sind auf dem heutigen `main` 732 Tests zu erwarten. Vorschlag: Beim Referenztestlauf (B5) die Ausgabe von `pip freeze` unter `docs/` ablegen. Dann ist der Windows-Stand festgeschrieben.

### A6 – Vorarbeiten für folgende Stufen (mittel)
Gibt es bereits konkrete, noch nicht eingecheckte Vorarbeiten für 2b (CUDA auf RTX 3080 Ti), 4 (MandelManager/TypeScript) oder 5a (Einfärber, insbesondere gebrochene Abbruchwerte und Farbzuordnung)? Bitte nur bereits bestehende Erkenntnisse oder Entwürfe nennen; keine neue Implementierung erforderlich.

Antwort (thojank, 28.11.2026): Keine Vorarbeiten außerhalb des Repos, weder Code noch Entwürfe. Für 2b gibt es eine Richtungsentscheidung vom Whiteboard: CuPy, mit der Rechenschleife in CUDA-C als Variante neben dem Python-Rechenkern. Für 4 und 5a gibt es nur das Stufenkonzept.

## B. Gemeinsam mit Richard zu klären (keine alleinige Aufgabe von thojank)

- B1: Abnahmekriterien anhand der fachlichen Spec Stufe 3 abgleichen: C4 iPad, C5 Elternbild/Größe, C6 Protokoll, C7 Autostart. Der Abnahmebericht verwendet abweichende Zuordnungen. Welche konkreten Prüfungen sind tatsächlich erfolgt und welche fehlen? C3 Wiederanlauf bleibt laut Bericht offen.
- B2: Nachweise für T7 (Firewall) und T8 (Netzlaufwerk X: beim Anmelden) sowie echten Windows-Autostart zusammentragen, soweit nicht schon erfolgt. Lokale Konfiguration nur ohne Zugangsdaten dokumentieren.
- B3: Tag stufe-2a dem tatsächlich abgenommenen Stand zuordnen und den noch offenen B9-Vermerk später abgleichen. stufe-3 bleibt bis zur bestätigten Vollabnahme eine Teilabnahmereferenz. Keine Tags ohne Freigabe ändern.
- B4: Reihenfolge der nächsten Arbeiten gemeinsam festlegen: Ergänzung Stufe 3, Stufe 2b, Stufe 4 oder die gemäß Stufenkonzept unabhängig mögliche Stufe 5a. Keine Änderung des Vorgehensmodells ohne Freigabe.
- B5: Referenztestlauf am übernommenen Stand und spätere erneute Sichtprüfung B5 aus Stufe 2a nach neuer Colorierung einplanen.

## Quellen und Umfang

[README](../README.md), [Stufenkonzept](../specs/stufenkonzept.md), [fachliche Spec 2a](../specs/stufe-2a-fachlich.md), [technische Spec 2a](../specs/stufe-2a-technisch.md), [fachliche Spec 3](../specs/stufe-3-fachlich.md), [technische Spec 3](../specs/stufe-3-technisch.md), [Abnahme 0](abnahme-stufe-0.md), [Abnahme 1](abnahme-stufe-1.md), [Abnahme 2a/3](abnahme-stufe-2a-und-3.md), [PR #6](https://github.com/b-riched/KI-Mandelbrot/pull/6), [PR #8](https://github.com/b-riched/KI-Mandelbrot/pull/8), [PR #9](https://github.com/b-riched/KI-Mandelbrot/pull/9).

Dies ist ein erster Fragenkatalog auf Basis der Verzeichnisinventur, zentraler Dokumente und ausgewählter Code-/Testdateien, keine vollständige Codeprüfung oder neue Abnahme. Weitere Fragen können nach vertiefter Analyse entstehen.
