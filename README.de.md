<div align="center">

# 🚀 AstroBench

### Benchmark für die Manipulation frei schwebender Objekte

**Ein bewegtes Objekt greifen und nach dem Kontakt sicher halten.**

[🌐 Projektseite](https://astroup.com/astrobench/) · [📖 Spezifikation (Englisch)](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Videos](https://astroup.com/astrobench/#videos) · [🐛 Issues](https://github.com/Brickkkkkk/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | **Deutsch**

[![CI](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Protocol](https://img.shields.io/badge/Protocol-0.1_draft-orange)](docs/protocol.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="Ein Roboterarm mit fester Basis nähert sich einer frei schwebenden Spule in einer Kabine. Zum Ansehen der Videos anklicken." width="760"></a>

</div>

## 🪐 Was ist AstroBench?

AstroBench untersucht, wie ein Roboterarm mit fester Basis frei schwebende Objekte in einer schwerelosen Kabine manipuliert. Ohne stützende Oberfläche kann die erste Berührung das Objekt wegstoßen oder in Drehung versetzen. Das Schließen des Greifers allein genügt nicht: Das Objekt muss sicher gehalten werden.

Die Bewertung trennt **Erfassen**, also den Aufbau eines stabilen Griffs, vom **Halten bis zum Episodenende**. Der umfassendere Aufgabenentwurf umfasst außerdem Kabinenmechanismen, Einstecken, Umorientieren und Verstauen.

Dieses Repository enthält das portable Evaluationsprotokoll: deterministische Episodenpläne, Trajektorienbewertung und vollständige Ergebnisaggregation. Es läuft auf einer CPU mit der Python-Standardbibliothek. Ein Umgebungsadapter liefert gemessene Trajektorien; die vollständige Umgebung und vortrainierte Policies sind nicht enthalten.

### ✨ Wesentliche Funktionen

- **Kontakt und Halten:** Bewertung beidseitigen Zielkontakts, gemessener Greiferschließung, relativer Bewegung und durchgehenden Haltens.
- **Reproduzierbare Pläne:** Objektidentität, Geometriegruppen, Bewegungsbedingungen und Protokolleinstellungen werden über Episoden-Hashes gebunden.
- **Explizite Abdeckung:** Aufgabenfehler, Laufzeitfehler und fehlende Episoden bleiben getrennt; für unvollständige Pläne wird kein vollständiger Makromittelwert ausgegeben.
- **Zwei Kameraperspektiven:** 40 ausgewählte Beispiele mit 20 Objekttypen aus Außen- und Kabinenansicht.
- **README in sieben Sprachen:** Die ausführliche technische Spezifikation ist auf Englisch und Chinesisch verfügbar.

## 🧭 Inhalt

- [🎬 Aufgabenvideos](#watch)
- [⚡ Schnellstart](#quickstart)
- [📏 Bewertungsverfahren](#evaluation)
- [🧩 Aufgabenentwurf](#tasks)
- [📊 Entwicklungsexperiment](#evidence)
- [🗂️ Repository-Struktur](#layout)
- [🛠️ Veröffentlichungsstand](#roadmap)
- [🤝 Mitwirken und zitieren](#contributing)

<a id="watch"></a>

## 🎬 Aufgabenvideos

| Bewegte Spule | Bewegter Schraubenschlüssel | Anfangs ruhende Spule |
| --- | --- | --- |
| [![Bewegte Spule](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Bewegter Schraubenschlüssel](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Anfangs ruhende Spule](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

In der [interaktiven Galerie](https://astroup.com/astrobench/#videos) lassen sich Objekte suchen, Kameras wechseln und Bewegungsdaten ansehen. Sie enthält **20 Objekttypen · 40 ausgewählte Episoden · 80 Videos**. Ausgewählte Beispiele ergeben keine Erfolgsrate eines Testsatzes. Historische Halte-Labels gehören zur jeweiligen Aufnahmeversion und werden getrennt vom aktuellen Endzustandsbewerter interpretiert.

<a id="quickstart"></a>

## ⚡ Schnellstart

**Voraussetzungen:** Python 3.11+, keine GPU und keine Laufzeitabhängigkeiten außerhalb der Standardbibliothek. Die folgenden Befehle verwenden eine POSIX-Shell.

### 1. Installieren und prüfen

```bash
git clone https://github.com/Brickkkkkk/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

Die Tests prüfen Protokoll und statistische Berechnungen.

### 2. Episodenplan erzeugen

```bash
astrobench plan examples/catalog.json --seed 42 --output plan.json
python -c 'import json; print(json.load(open("plan.json"))["episodes"][0]["episode_id"])'
```

Der mitgelieferte Katalog ist eine synthetische Eingabe zum Schnittstellentest, ohne zugehörige physische Assets. Für ein Experiment werden geprüfte Assets mit `object_id`, `asset_sha256`, `geometry_group` und `split` benötigt. Der Planer lehnt Assets oder Geometriegruppen ab, die sich über mehrere Datensplits verteilen.

### 3. Gemessene Trajektorie bewerten

```bash
astrobench score plan.json EPISODE_ID trace.json --output episode-result.json
```

Zuerst `trace.json` mit dem Umgebungsadapter exportieren und `EPISODE_ID` durch die zuvor ausgegebene Kennung ersetzen. Die Trajektorie enthält `episode_id`, `spec_hash` und `samples`. Jeder Messpunkt enthält Zeitstempel, Zielkontaktkräfte pro Finger, gemessene Schließung, verbotenen Kontakt, Verlassen des Arbeitsraums sowie relative Geschwindigkeiten und Pose. Siehe [Feldvertrag (Englisch)](docs/protocol.md#trace-and-adapter-contract).

### 4. Ergebnisse zusammenfassen

```bash
python -c 'import json; json.dump([json.load(open("episode-result.json"))], open("results.json", "w"))'
astrobench report plan.json results.json --output report.json
```

Dieses Beispiel fasst nur ein Episodenergebnis in einem Array zusammen. Ein Plan mit mehreren Episoden wird daher korrekt als unvollständig ausgewiesen. Für einen vollständigen Bericht müssen alle geplanten Ergebnisse derselben Policy/desselben Checkpoints im JSON-Array stehen. Die CLI überschreibt keine bestehenden Ausgabedateien; für neue Läufe neue Pfade verwenden.

<a id="evaluation"></a>

## 📏 Bewertungsverfahren

Geprüfter Asset-Katalog → registrierter Plan mit Identitäts-Hashes → gemessene Trajektorie des Adapters → Bewertung von Erfassen und Halten bis zum Ende → Erfolg, Abdeckung und Unsicherheit. Der öffentliche Entwurf heißt `astrobench.capture-retain/0.1-draft`.

| Einstellung | Wert |
| --- | --- |
| Episodendauer | 12 s |
| Durchgehendes Haltefenster | 1.0 s verstrichene Zeit laut Zeitstempeln |
| Nominelle Messfrequenz / maximale Lücke | 50 Hz / 25 ms |
| Kontaktkraft am Ziel | Mindestens 0.5 N pro Finger |
| Maximale relative Linear- / Winkelgeschwindigkeit | 0.02 m/s / 0.2 rad/s |
| Maximale relative Positions- / Orientierungsabweichung | 0.01 m / 0.1 rad |

**Frühes Erfassen mit anschließendem Verlust zählt nicht als Erfolg.** Ein durchgehend gültiges Haltefenster muss am Episodenende enden. Ungültige oder abgeschnittene Logs werden abgewiesen. Ein reguläres Zeitlimit zählt als Aufgabenfehler; Laufzeitfehler und fehlende Episoden werden separat gemeldet.

Der Planer bietet `static`, `drift`, `tumble` und `fast_tumble`. Diese Bewegungsbedingungen sind vorläufig und noch kein festgeschriebener Generalisierungsbenchmark. Die Schwellenwerte müssen mit dem Umgebungsadapter kalibriert werden. Der Bewerter prüft Logs; der Adapter muss physische Konfiguration und Sensorzuordnung verifizieren.

📖 [Spezifikation (Englisch)](https://astroup.com/astrobench/docs/current/index.html) · [Protocol reference (English)](docs/protocol.md)

<a id="tasks"></a>

## 🧩 Aufgabenentwurf

| Kategorie | Aufgabenfamilien | Abschlussnachweis |
| --- | --- | --- |
| Greifen frei schwebender Objekte | Erfassen und halten | Beidseitiger Kontakt, tatsächliche Schließung und Halten |
| Mechanismen bedienen | Türen, Schubladen, Tasten, Drehknöpfe/Ventile, Hebel | Gelenkzustand oder Weg, Richtung und Phasenfolge |
| Präzises Fügen | Stifte einsetzen, Steckverbinder, Module einsetzen | Ausrichtung, Einstecktiefe und Sitz |
| Objekte manipulieren | Umorientieren, verstauen und schließen | Zielpose oder geordnetes Platzieren, Loslassen und Schließen |

Der Entwurf mit 11 Aufgabenfamilien geht über die aktuellen Greifvideos und den öffentlichen Greifbewerter hinaus. Andere Familien benötigen eigene Validierung und aufgabenspezifische Bewerter. Offizielle Objekt- und Bewegungssplits sind noch nicht festgelegt.

<a id="evidence"></a>

## 📊 Entwicklungsexperiment

Ein gepaarter Pilotversuch mit einem Würfel umfasst 40 Episoden: ein eingefrorener ACT-Checkpoint und eine angepasste Zustandsregelung als Referenz, zehn Entwicklungspositionen und zwei Bewegungsbedingungen, ohne erneutes Training.

| Methode | Anfangszustand | Griff erreicht | Bis zum Ende gehalten |
| --- | --- | --- | --- |
| ACT | Ruhend | 8 / 10 | 3 / 10 |
| ACT | Bewegt | 6 / 10 | 0 / 10 |
| Zustandsbasierte Referenz | Ruhend | 8 / 10 | 8 / 10 |
| Zustandsbasierte Referenz | Bewegt | 0 / 10 | 0 / 10 |

Der Pilot verwendet ein eigenes **natives Protokoll mit 15 Hz und 20 Sekunden**, nicht den öffentlichen 12-Sekunden-Bewerter. Die Referenz nutzt privilegierte Zustandsinformationen. Alle ihre bewegten Episoden endeten an einer controllerspezifischen Grenze des Tracking-Arbeitsraums. In ruhenden Episoden entstand der Griff später, sodass weniger Zeit zur Beobachtung des Haltens blieb. Dies sind Entwicklungsdiagnosen, keine Rangliste bei gleichen Informationen und kein Generalisierungsergebnis über 20 Objekte. Siehe [Aufbau, Konfidenzintervalle und Einordnung (Englisch)](https://astroup.com/astrobench/docs/current/index.html#pilot).

<a id="layout"></a>

## 🗂️ Repository-Struktur

```text
AstroBench/
├── astrobench/
├── docs/protocol.md
├── examples/catalog.json
├── tests/
├── .github/workflows/
├── README.md
└── README.*.md
```

`astrobench/`: Pläne, Bewertung, Aggregation und CLI; `docs/protocol.md`: Trajektorienvertrag; `examples/`: synthetischer Katalog; `tests/`: Protokoll- und Statistiktests; `.github/workflows/`: CI; `README.*.md`: sprachspezifische Anleitungen.

<a id="roadmap"></a>

## 🛠️ Veröffentlichungsstand

- [x] Portables Paket für Planung, Bewertung und Aggregation
- [x] Protokolltests und GitHub Actions CI
- [x] Projektseite und Spezifikation auf Englisch/Chinesisch, mehrsprachiges README
- [x] Ausgewählte Greifvideos aus zwei Perspektiven
- [x] Gepaarter Entwicklungsversuch mit einem Würfel
- [ ] Vollständig portable Umgebung und Asset-Verteilung
- [ ] Feste Objektsplits und kalibrierte Bewegungsbedingungen
- [ ] Breitere Baseline-Auswertung und Halteprüfungen mit gleicher Beobachtungsdauer
- [ ] Veröffentlichung des Papers

Automatische Datenerfassung, Demonstrations-/Lehrer-Policies, Trainingspipelines und Rohdatensätze gehören nicht zum Veröffentlichungsumfang dieses Repositorys.

<a id="contributing"></a>

## 🤝 Mitwirken und zitieren

Bei Bewertungsgrenzfällen oder unklaren Schnittstellen bitte ein [Issue](https://github.com/Brickkkkkk/AstroBench/issues) mit Protokollversion, minimal reproduzierbarer Trajektorie und erwartetem Ergebnis erstellen. Bei Änderungen an Schwellenwerten oder Zeitsemantik erläutern, wie bestehende Ergebnisse versioniert werden. Vor einem PR die Tests ausführen.

Das Paper wird überarbeitet und hat noch keine arXiv-Kennung. Bis eine formale Zitierangabe verfügbar ist, bitte Repository-URL sowie den genauen verwendeten Commit und die Protokollversion angeben.

Verwandte Arbeit: [Space Robotics Bench](https://arxiv.org/abs/2509.23328).

