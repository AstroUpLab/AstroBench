<div align="center">

# 🚀 AstroBench

### Benchmark für die Manipulation frei schwebender Objekte

[🌐 Website](https://astroup.com/astrobench/) · [📖 Docs](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Videos](https://astroup.com/astrobench/#videos) · [🐛 Issues](https://github.com/AstroUpLab/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![Tests](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Objects](https://img.shields.io/badge/Default-20_classes-227799)](docs/objects.md)
[![Objaverse](https://img.shields.io/badge/Objaverse-8414_objects-448844)](docs/objects.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="AstroBench free-floating grasping" width="760"></a>

</div>

AstroBench untersucht das Erfassen und Halten frei schwebender Objekte sowie Manipulationsaufgaben in Raumstationskabinen. Kontakt kann ein Objekt verschieben oder drehen; der Griff muss bis zum Ende der Episode halten.

## ⚡ Schnellstart

Das Paket bietet Objektauswahl, reproduzierbare Episodenpläne, Trajektorienbewertung und Ergebnisaggregation. Python 3.11+ mit Standardbibliothek.

```bash
git clone https://github.com/AstroUpLab/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

## 🛠️ Arbeitsbereiche im Weltraum

**MELFI V6** umfasst das Umsetzen, Einsetzen und Entnehmen von Probenkarten sowie das Öffnen und Schließen der Deckel. **RRM TB1** umfasst das Entfernen und Verstauen von FDV1- / SMA-Kappen sowie das Lösen und Anziehen unverlierbarer Schrauben. Modelle, Werkzeuge, Aufgabendefinitionen und Regeln zur Bewertung gemessener Trajektorien sind enthalten.

[📖 Anleitung und Aufgaben](docs/workcells.md) · [🧊 MELFI-Modelle](assets/workcells/melfi_v6/) · [🛰️ RRM-Modelle](assets/workcells/rrm_tb1/) · [🎬 FDV1](docs/media/fdv1.mp4) · [🎬 SMA](docs/media/sma.mp4) · [🎬 Schrauben](docs/media/captive.mp4)

Die RRM-Videos zeigen die Kappen- und Schraubenmechanik im ursprünglichen Tischaufbau.

```bash
astrobench workcells --output workcells.json
astrobench workcell-plan --workcell all --repeats 10 --seed 42 --output workcell-plan.json
```

## 💬 Aufgaben und Prompts

Beim Greifen lautet die Anweisung `Capture the {object_name} and hold it securely.` für die vier Bedingungen `static`, `drift`, `tumble` und `fast_tumble`. Die Arbeitsbereiche ergänzen 9 Aufgaben mit 29 Kombinationen aus Aufgabe und Ziel. `{target_name}` wird durch den Namen des Ziels ersetzt. Das RRM-Panel ist an der Wand befestigt; der Roboter steht mittig davor auf einer Bodenplatte.

| Aufgaben-ID | Englische Prompt-Vorlage |
| --- | --- |
| `card_transfer_to_mouth` | Move the card to the opening of the {target_name} and hold it aligned. |
| `card_insert` | Insert the card fully into the {target_name}, release it, and leave it retained inside. |
| `card_extract` | Remove the card from the {target_name} and hold it clear of the opening. |
| `lid_open` | Open the lid of the {target_name} and leave it open. |
| `lid_close` | Close and latch the lid of the {target_name}, then withdraw the gripper. |
| `fdv1_remove_stow` | Unscrew and remove the {target_name}, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `sma_remove_stow` | Unscrew and remove the {target_name}, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `captive_loosen` | Loosen the {target_name} without releasing it from the panel and hold it in the loosened position. |
| `captive_tighten` | Tighten the {target_name} until it is seated, keep it captive, and withdraw the driver. |

```bash
astrobench task-prompts --output task-prompts.json
astrobench task-prompts --object-set objaverse8414 --scope capture --output objaverse-prompts.json
```

[📋 Alle Aufgaben, Ziele und Anweisungen](docs/tasks.md) · [📋 中文任务目录](docs/tasks.zh-CN.md)

## 🧰 Objektsammlungen

Standard: **20 Klassen**. Die **Objaverse-Erweiterung umfasst 8.414 Objekte**: Werkzeuge, Behälter, tragbare Elektronik, mechanische Teile und Kabinenbedarf. Sie enthält 51 LVIS-Kategorien sowie Objekte ohne LVIS-Zuordnung.

Das Inventar enthält Objekt-IDs, Namen, Kategorien, Quellenlinks und Urheberangaben.

```bash
astrobench objects --output core20.json
astrobench objects --object-set objaverse8414 --output objaverse8414.json
```

[📖 Object catalog & selection](docs/objects.md) · [📖 物体集与筛选](docs/objects.zh-CN.md)

## 🛰️ Kabinenszenen

| ID | Cabin |
| --- | --- |
| `iss_jpm` | Kibo / JPM |
| `iss_us_lab` | US Laboratory |
| `iss_eu_lab` | European Laboratory |
| `iss_node2` | Node 2 |
| `iss_cupola` | Node 3 workcell near Cupola |

Jede Kabinenumgebung kann für statische und dynamische Greifaufgaben verwendet werden. MELFI und RRM werden über die separate [Arbeitsbereich-Schnittstelle](docs/workcells.md) ausgewählt; die Hardware wird entsprechend der jeweiligen Aufgabenanordnung montiert.

```bash
astrobench scenes --output scenes.json
```

## 📏 Protokollwerkzeuge

Der Beispielkatalog zeigt die Asset-Schnittstelle. Eigene Kataloge enthalten object_id, asset_sha256, geometry_group und split. Messfelder stehen in der Protokollreferenz.

```bash
astrobench plan examples/catalog.json --object-set custom --seed 42 --output plan.json
astrobench plan assets.json --seed 42 --output core20-plan.json
astrobench plan assets.json --object-set objaverse8414 --seed 42 --output expanded-plan.json
```

```bash
astrobench score plan.json EPISODE_ID trace.json --output episode-result.json
astrobench report plan.json results.json --output report.json
```

[📖 Protocol reference](docs/protocol.md)

## 🎬 Ressourcen

| Dynamic spool | Dynamic wrench | Static spool |
| :---: | :---: | :---: |
| [![Spool](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Wrench](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Spool](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

[Objaverse](https://objaverse.allenai.org/) · [NASA Astrobee ISS assets](https://github.com/nasa/astrobee_media/tree/master/astrobee_iss) · [Space Robotics Bench](https://arxiv.org/abs/2509.23328)

## 📚 Zitierung

Wenn Sie AstroBench in Ihrer Forschung verwenden, zitieren Sie das Projekt mit folgendem BibTeX:

```bibtex
@misc{astrouplab2026astrobench,
  author       = {{AstroUpLab}},
  title        = {{AstroBench}: Free-floating Manipulation Benchmark},
  year         = {2026},
  howpublished = {GitHub repository},
  url          = {https://github.com/AstroUpLab/AstroBench}
}
```

Bitte nennen Sie beim Zitieren die Repository-URL und die Commit-ID.
