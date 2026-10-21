<div align="center">

# 🚀 AstroBench

### Free-floating Manipulation Benchmark

[🌐 Website](https://astroup.com/astrobench/) · [📖 Docs](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Videos](https://astroup.com/astrobench/#videos) · [🐛 Issues](https://github.com/AstroUpLab/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![Tests](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Objects](https://img.shields.io/badge/Default-20_classes-227799)](docs/objects.md)
[![Objaverse](https://img.shields.io/badge/Objaverse-8414_objects-448844)](docs/objects.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="AstroBench free-floating grasping" width="760"></a>

</div>

AstroBench studies capture and retention of free-floating objects, together with cabin manipulation tasks. Contact can move or rotate the target; successful grasping requires the object to stay secure through the end of the episode.

## ⚡ Quick start

The package provides object selection, deterministic episode plans, trajectory scoring and result aggregation. Python 3.11+; standard-library runtime.

```bash
git clone https://github.com/AstroUpLab/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

## 🛠️ Space workcells

Two workcells connect space hardware to specific manipulation goals: **MELFI V6** for sample storage and **RRM TB1** for servicing caps and captive screws. Each includes editable Blender models, portable GLB assets, named parts, task definitions and measurement-based scoring.

| MELFI V6 — sample storage | RRM TB1 — servicing panel |
| :---: | :---: |
| <img src="docs/media/melfi.png" alt="MELFI V6: two narrow boxes and one wide box mounted along the wall" width="420"> | <img src="docs/media/rrm.png" alt="RRM TB1 servicing panel with caps, captive screws and tools" width="420"> |
| [GLB](assets/workcells/melfi_v6/melfi_v6.glb) · [Blender](assets/workcells/melfi_v6/melfi_v6.blend) · [Parts](assets/workcells/melfi_v6/parts.json) | [GLB](assets/workcells/rrm_tb1/rrm_tb1.glb) · [Blender](assets/workcells/rrm_tb1/rrm_tb1.blend) · [Parts](assets/workcells/rrm_tb1/parts.json) |

| Workcell | Task | Completion goal |
| --- | --- | --- |
| MELFI V6 | Transfer sample card | Hold the card at the selected box opening. |
| MELFI V6 | Insert sample card | Seat and retain the card in the selected box, then release it. |
| MELFI V6 | Extract sample card | Clear the selected box opening while retaining the card. |
| MELFI V6 | Open lid | Open the selected lid to its target angle. |
| MELFI V6 | Close lid | Close and latch the selected lid. |
| RRM TB1 | Remove and stow FDV1 cap | Unscrew, withdraw and secure the cap in its receiver. |
| RRM TB1 | Remove and stow selected SMA cap | Select the requested cap, unscrew it and secure it in its receiver. |
| RRM TB1 | Loosen captive screw | Reach the loosened position while the screw remains captive. |
| RRM TB1 | Tighten captive screw | Seat the screw and withdraw the tool. |

```bash
astrobench workcells --output workcells.json
astrobench workcell-check-assets assets/workcells --output asset-check.json
astrobench workcell-plan --workcell all --repeats 10 --seed 42 --output workcell-plan.json
```

[📖 Tasks, setup and scoring](docs/workcells.md) · [📖 中文指南](docs/workcells.zh-CN.md) · [🎬 FDV1](docs/media/fdv1.mp4) · [🎬 SMA](docs/media/sma.mp4) · [🎬 Captive screw](docs/media/captive.mp4)

The hardware follows NASA / ESA references, with source links and modeling notes in the [workcell guide](docs/workcells.md).

## 🧰 Object collections

Default: **20 classes**. Choose **Objaverse: 8,414 objects** for the expanded inventory. The expansion contains tools, containers, portable electronics, mechanical parts and cabin supplies. It represents 51 LVIS category labels plus unlabeled objects.

The inventory includes object IDs, names, category labels, source links and author attribution. Select objects with the commands below.

```bash
astrobench objects --output core20.json
astrobench objects --object-set objaverse8414 --output objaverse8414.json
```

[📖 Object catalog & selection](docs/objects.md) · [📖 物体集与筛选](docs/objects.zh-CN.md)

## 🛰️ Cabin scenes

| ID | Cabin |
| --- | --- |
| `iss_jpm` | Kibo / JPM |
| `iss_us_lab` | US Laboratory |
| `iss_eu_lab` | European Laboratory |
| `iss_node2` | Node 2 |
| `iss_cupola` | Node 3 workcell near Cupola |

Each cabin background can be used with the static and dynamic grasping tracks. Select MELFI and RRM through the separate [workcell task interface](docs/workcells.md), and install their hardware according to the task layout.

```bash
astrobench scenes --output scenes.json
```

## 📏 Protocol tools

The example catalog demonstrates the asset interface. For your catalog, provide object_id, asset_sha256, geometry_group and split; see the protocol reference for measurement fields.

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

## 🎬 Resources

| Dynamic spool | Dynamic wrench | Static spool |
| :---: | :---: | :---: |
| [![Spool](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Wrench](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Spool](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

[Objaverse](https://objaverse.allenai.org/) · [NASA Astrobee ISS assets](https://github.com/nasa/astrobee_media/tree/master/astrobee_iss) · [Space Robotics Bench](https://arxiv.org/abs/2509.23328)

## 📚 Citation

If you use AstroBench in your research, please cite the project as follows:

```bibtex
@misc{astrouplab2026astrobench,
  author       = {{AstroUpLab}},
  title        = {{AstroBench}: Free-floating Manipulation Benchmark},
  year         = {2026},
  howpublished = {GitHub repository},
  url          = {https://github.com/AstroUpLab/AstroBench}
}
```

Use the repository URL and commit identifier when citing this version.
