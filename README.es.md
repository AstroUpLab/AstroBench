<div align="center">

# 🚀 AstroBench

### Benchmark de manipulación de objetos en flotación libre

[📄 Artículo](https://arxiv.org/abs/2610.31064) · [🌐 Website](https://astroup.com/astrobench/) · [📖 Docs](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Videos](https://astroup.com/astrobench/#videos) · [🐛 Issues](https://github.com/AstroUpLab/AstroBench/issues)

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

## 🛠️ Puestos de trabajo espaciales

**MELFI V6** incorpora el traslado, la inserción y la extracción de tarjetas de muestras, además de la apertura y el cierre de tapas. **RRM TB1** incorpora la retirada y el almacenamiento de tapas FDV1 / SMA y el aflojado y apriete de tornillos cautivos. Se incluyen modelos, herramientas, definiciones de tareas y evaluación de trayectorias medidas.

[📖 Guía y tareas](docs/workcells.md) · [🧊 Modelos MELFI](assets/workcells/melfi_v6/) · [🛰️ Modelos RRM](assets/workcells/rrm_tb1/) · [🎬 FDV1](docs/media/fdv1.mp4) · [🎬 SMA](docs/media/sma.mp4) · [🎬 Tornillos](docs/media/captive.mp4)

Los vídeos RRM muestran los mecanismos de tapas y tornillos en la disposición original sobre mesa.

```bash
astrobench workcells --output workcells.json
astrobench workcell-plan --workcell all --repeats 10 --seed 42 --output workcell-plan.json
```

## 💬 Tareas e instrucciones

El agarre usa `Capture the {object_name} and hold it securely.` en cuatro condiciones: `static`, `drift`, `tumble` y `fast_tumble`. Los puestos de trabajo añaden 9 tareas y 29 combinaciones de tarea y objetivo. `{target_name}` se sustituye por el nombre del objetivo. El panel RRM se fija a la pared y el brazo se sitúa enfrente, sobre una placa de suelo.

| ID de tarea | Plantilla de instrucción en inglés |
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

[📋 Todas las tareas, objetivos e instrucciones](docs/tasks.md) · [📋 中文任务目录](docs/tasks.zh-CN.md)

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

Cada fondo de cabina puede utilizarse con las tareas de agarre estático y dinámico. MELFI y RRM se seleccionan mediante la [interfaz de puestos de trabajo](docs/workcells.md), instalando el hardware según la disposición de cada tarea.

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

Si utiliza AstroBench en su investigación, cite nuestro artículo:

[arXiv](https://arxiv.org/abs/2610.31064) · [PDF](https://arxiv.org/pdf/2610.31064) · [BibTeX](CITATION.bib)

```bibtex
@misc{wang2026astrobench,
  title         = {{AstroBench}: Benchmarking Free-Floating Capture and Space Robotic Manipulation},
  author        = {Zizhe Wang and Jia Deng and Xin Lu and Zehao Jia and Yi Huang and Yao Zhu},
  year          = {2026},
  eprint        = {2610.31064},
  archivePrefix = {arXiv},
  primaryClass  = {cs.RO},
  doi           = {10.48550/arXiv.2610.31064},
  url           = {https://arxiv.org/abs/2610.31064}
}
```

Al citar esta versión, incluya la URL del repositorio y el identificador del commit.

