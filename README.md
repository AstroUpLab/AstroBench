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

Each cabin configuration reuses the static/dynamic grasping tracks and ten operation task families.

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

Use the repository URL and commit identifier when citing this version.
