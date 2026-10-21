<div align="center">

# 🚀 AstroBench

### Benchmark de manipulation d’objets en flottement libre

[🌐 Website](https://astroup.com/astrobench/) · [📖 Docs](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Videos](https://astroup.com/astrobench/#videos) · [🐛 Issues](https://github.com/AstroUpLab/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![Tests](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Objects](https://img.shields.io/badge/Default-20_classes-227799)](docs/objects.md)
[![Objaverse](https://img.shields.io/badge/Objaverse-8414_objects-448844)](docs/objects.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="AstroBench free-floating grasping" width="760"></a>

</div>

AstroBench étudie la capture et le maintien d’objets en flottement libre ainsi que les tâches de manipulation en cabine. Le contact peut déplacer ou faire tourner la cible ; la prise doit tenir jusqu’à la fin de l’épisode.

## ⚡ Démarrage rapide

Le package fournit la sélection d’objets, des plans reproductibles, la notation des trajectoires et l’agrégation des résultats. Python 3.11+ et bibliothèque standard.

```bash
git clone https://github.com/AstroUpLab/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

## 🛠️ Postes de travail spatiaux

**MELFI V6** propose le transfert, l’insertion et le retrait de cartes d’échantillons, ainsi que l’ouverture et la fermeture des couvercles. **RRM TB1** propose le retrait et le rangement des bouchons FDV1 / SMA, ainsi que le desserrage et le serrage des vis captives. Les modèles, outils, définitions des tâches et règles d’évaluation des trajectoires mesurées sont fournis.

[📖 Guide et tâches](docs/workcells.md) · [🧊 Modèles MELFI](assets/workcells/melfi_v6/) · [🛰️ Modèles RRM](assets/workcells/rrm_tb1/) · [🎬 FDV1](docs/media/fdv1.mp4) · [🎬 SMA](docs/media/sma.mp4) · [🎬 Vis](docs/media/captive.mp4)

```bash
astrobench workcells --output workcells.json
astrobench workcell-plan --workcell all --repeats 10 --seed 42 --output workcell-plan.json
```

## 🧰 Collections d’objets

Par défaut : **20 classes**. L’extension **Objaverse comprend 8 414 objets** : outils, récipients, appareils portables, pièces mécaniques et fournitures de cabine. Elle couvre 51 étiquettes LVIS et des objets sans étiquette.

L’inventaire conserve les identifiants, noms, catégories, liens sources et attributions aux auteurs.

```bash
astrobench objects --output core20.json
astrobench objects --object-set objaverse8414 --output objaverse8414.json
```

[📖 Object catalog & selection](docs/objects.md) · [📖 物体集与筛选](docs/objects.zh-CN.md)

## 🛰️ Scènes de cabine

| ID | Cabin |
| --- | --- |
| `iss_jpm` | Kibo / JPM |
| `iss_us_lab` | US Laboratory |
| `iss_eu_lab` | European Laboratory |
| `iss_node2` | Node 2 |
| `iss_cupola` | Node 3 workcell near Cupola |

Chaque décor de cabine peut accueillir les tâches de préhension statiques et dynamiques. MELFI et RRM se sélectionnent dans l’[interface des postes de travail](docs/workcells.md), avec le matériel installé selon la disposition de chaque tâche.

```bash
astrobench scenes --output scenes.json
```

## 📏 Outils du protocole

Le catalogue d’exemple illustre l’interface des actifs. Renseignez object_id, asset_sha256, geometry_group et split dans votre catalogue. Les mesures sont décrites dans le protocole.

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

## 🎬 Ressources

| Dynamic spool | Dynamic wrench | Static spool |
| :---: | :---: | :---: |
| [![Spool](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Wrench](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Spool](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

[Objaverse](https://objaverse.allenai.org/) · [NASA Astrobee ISS assets](https://github.com/nasa/astrobee_media/tree/master/astrobee_iss) · [Space Robotics Bench](https://arxiv.org/abs/2509.23328)

## 📚 Citation

Si vous utilisez AstroBench dans vos recherches, veuillez citer le projet avec le BibTeX suivant :

```bibtex
@misc{astrouplab2026astrobench,
  author       = {{AstroUpLab}},
  title        = {{AstroBench}: Free-floating Manipulation Benchmark},
  year         = {2026},
  howpublished = {GitHub repository},
  url          = {https://github.com/AstroUpLab/AstroBench}
}
```

Pour citer cette version, indiquez l’URL du dépôt et l’identifiant du commit.
