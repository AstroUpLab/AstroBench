<div align="center">

# 🚀 AstroBench

### 自由浮遊物体の操作ベンチマーク

[📄 論文](https://arxiv.org/abs/2610.31064) · [🌐 Website](https://astroup.com/astrobench/) · [📖 Docs](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Videos](https://astroup.com/astrobench/#videos) · [🐛 Issues](https://github.com/AstroUpLab/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![Tests](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Objects](https://img.shields.io/badge/Default-20_classes-227799)](docs/objects.md)
[![Objaverse](https://img.shields.io/badge/Objaverse-8414_objects-448844)](docs/objects.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="AstroBench free-floating grasping" width="760"></a>

</div>

AstroBench は自由浮遊物体の捕獲と保持、および船内操作タスクを扱います。接触によって対象が移動・回転するため、エピソード終了まで保持することを評価します。

## ⚡ クイックスタート

物体選択、再現可能なエピソード計画、軌跡採点、結果集計を提供します。Python 3.11+ と標準ライブラリで動作します。

```bash
git clone https://github.com/AstroUpLab/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

## 🛠️ 宇宙作業セル

**MELFI V6** の試料カードの移動・挿入・取り出しと蓋の開閉、**RRM TB1** の FDV1 / SMA キャップの取り外し・保管と脱落防止ねじの締緩を収録しています。モデル、工具、タスク定義、軌跡の採点手順を公開しています。

[📖 作業セルガイド・タスク一覧](docs/workcells.md) · [🧊 MELFI モデル](assets/workcells/melfi_v6/) · [🛰️ RRM モデル](assets/workcells/rrm_tb1/) · [🎬 FDV1](docs/media/fdv1.mp4) · [🎬 SMA](docs/media/sma.mp4) · [🎬 ねじ](docs/media/captive.mp4)

RRM の動画は、元の卓上配置でのキャップとねじの機構動作を示しています。

```bash
astrobench workcells --output workcells.json
astrobench workcell-plan --workcell all --repeats 10 --seed 42 --output workcell-plan.json
```

## 💬 タスクとプロンプト

把持には `Capture the {object_name} and hold it securely.` を使い、`static`、`drift`、`tumble`、`fast_tumble` の4条件を比較します。作業セルは9タスク・29のタスクと対象の組み合わせです。下表の `{target_name}` は各対象の名前に置き換えます。RRM パネルは壁面に固定し、ロボットはその正面の床板に設置します。

| タスク ID | 英語のプロンプトテンプレート |
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

[📋 全タスク・対象・英語指示](docs/tasks.md) · [📋 中文任务目录](docs/tasks.zh-CN.md)

## 🧰 物体セット

既定は **20 クラス**。拡張セットとして **Objaverse の 8,414 物体**を選択できます。工具、容器、携帯電子機器、機械部品、船内用品を含み、51 の LVIS ラベルと未分類物体から構成されます。

物体 ID、名前、カテゴリ、出典、作者を記録した一覧を出力します。

```bash
astrobench objects --output core20.json
astrobench objects --object-set objaverse8414 --output objaverse8414.json
```

[📖 Object catalog & selection](docs/objects.md) · [📖 物体集与筛选](docs/objects.zh-CN.md)

## 🛰️ 船内シーン

| ID | Cabin |
| --- | --- |
| `iss_jpm` | Kibo / JPM |
| `iss_us_lab` | US Laboratory |
| `iss_eu_lab` | European Laboratory |
| `iss_node2` | Node 2 |
| `iss_cupola` | Node 3 workcell near Cupola |

各船内背景は静的・動的把持に利用できます。MELFI と RRM は専用の[作業セルタスク](docs/workcells.md)から選択し、タスクの配置に従って機材を設置します。

```bash
astrobench scenes --output scenes.json
```

## 📏 プロトコルツール

サンプルはアセットのインターフェースを示します。カタログには object_id、asset_sha256、geometry_group、split を指定します。測定項目はプロトコル文書を参照してください。

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

## 🎬 リソース

| Dynamic spool | Dynamic wrench | Static spool |
| :---: | :---: | :---: |
| [![Spool](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Wrench](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Spool](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

[Objaverse](https://objaverse.allenai.org/) · [NASA Astrobee ISS assets](https://github.com/nasa/astrobee_media/tree/master/astrobee_iss) · [Space Robotics Bench](https://arxiv.org/abs/2509.23328)

## 📚 引用

研究で AstroBench を使用する場合は、以下の論文を引用してください。

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

引用時にはリポジトリ URL とコミット ID を記録してください。

