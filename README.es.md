<div align="center">

# 🚀 AstroBench

### Benchmark de manipulación de objetos en flotación libre

[🌐 Website](https://astroup.com/astrobench/) · [📖 Docs](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Videos](https://astroup.com/astrobench/#videos) · [🐛 Issues](https://github.com/AstroUpLab/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![Tests](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Objects](https://img.shields.io/badge/Default-20_classes-227799)](docs/objects.md)
[![Objaverse](https://img.shields.io/badge/Objaverse-8414_objects-448844)](docs/objects.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="AstroBench free-floating grasping" width="760"></a>

</div>

AstroBench estudia la captura y retención de objetos en flotación libre y las tareas de manipulación en cabina. El contacto puede desplazar o hacer girar el objeto; el agarre debe mantenerse hasta el final del episodio.

## ⚡ Inicio rápido

El paquete permite seleccionar objetos, generar planes reproducibles, puntuar trayectorias y agregar resultados. Requiere Python 3.11+ y su biblioteca estándar.

```bash
git clone https://github.com/AstroUpLab/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

## 🧰 Colecciones de objetos

Por defecto: **20 clases**. La extensión **Objaverse contiene 8.414 objetos**: herramientas, recipientes, dispositivos portátiles, piezas mecánicas y suministros de cabina. Incluye 51 etiquetas LVIS y objetos sin etiqueta.

El inventario conserva identificadores, nombres, categorías, enlaces de origen y atribución de autoría.

```bash
astrobench objects --output core20.json
astrobench objects --object-set objaverse8414 --output objaverse8414.json
```

[📖 Object catalog & selection](docs/objects.md) · [📖 物体集与筛选](docs/objects.zh-CN.md)

## 🛰️ Escenas de cabina

| ID | Cabin |
| --- | --- |
| `iss_jpm` | Kibo / JPM |
| `iss_us_lab` | US Laboratory |
| `iss_eu_lab` | European Laboratory |
| `iss_node2` | Node 2 |
| `iss_cupola` | Node 3 workcell near Cupola |

Cada configuración de cabina comparte los agarres estáticos y dinámicos y diez familias de tareas de manipulación.

```bash
astrobench scenes --output scenes.json
```

## 📏 Herramientas del protocolo

El catálogo de ejemplo muestra la interfaz de activos. Proporcione object_id, asset_sha256, geometry_group y split en su catálogo. Los campos de medición se describen en el protocolo.

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

## 🎬 Recursos

| Dynamic spool | Dynamic wrench | Static spool |
| :---: | :---: | :---: |
| [![Spool](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Wrench](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Spool](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

[Objaverse](https://objaverse.allenai.org/) · [NASA Astrobee ISS assets](https://github.com/nasa/astrobee_media/tree/master/astrobee_iss) · [Space Robotics Bench](https://arxiv.org/abs/2509.23328)

## 📚 Cita

Si utiliza AstroBench en su investigación, cite el proyecto con el siguiente BibTeX:

```bibtex
@misc{astrouplab2026astrobench,
  author       = {{AstroUpLab}},
  title        = {{AstroBench}: Free-floating Manipulation Benchmark},
  year         = {2026},
  howpublished = {GitHub repository},
  url          = {https://github.com/AstroUpLab/AstroBench}
}
```

Al citar esta versión, incluya la URL del repositorio y el identificador del commit.
