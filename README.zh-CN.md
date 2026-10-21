<div align="center">

# 🚀 AstroBench

### 太空自由漂浮操作基准

[🌐 Website](https://astroup.com/astrobench/) · [📖 Docs](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Videos](https://astroup.com/astrobench/#videos) · [🐛 Issues](https://github.com/AstroUpLab/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![Tests](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Objects](https://img.shields.io/badge/Default-20_classes-227799)](docs/objects.md)
[![Objaverse](https://img.shields.io/badge/Objaverse-8414_objects-448844)](docs/objects.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="AstroBench free-floating grasping" width="760"></a>

</div>

AstroBench 研究自由漂浮物体的捕获与保持，以及舱内操作任务。接触会改变目标的位置和转动状态；抓取成功要求物体持续保持在夹爪中，直至回合结束。

## ⚡ 快速开始

提供物体选择、确定性回合计划、轨迹评分与结果汇总。需要 Python 3.11+，运行依赖为 Python 标准库。

```bash
git clone https://github.com/AstroUpLab/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

## 🛠️ 太空操作工作位

新增两组围绕真实航天硬件设计的操作工作位：**MELFI V6** 用于样本收纳，**RRM TB1** 用于接口帽与防脱螺钉维护。每组提供可编辑 Blender 模型、通用 GLB 资产、部件命名、任务定义与基于测量状态的评分。

| MELFI V6 — 样本收纳 | RRM TB1 — 卫星维修面板 |
| :---: | :---: |
| <img src="docs/media/melfi.png" alt="MELFI V6：两窄一宽置物盒沿墙安装" width="420"> | <img src="docs/media/rrm.png" alt="RRM TB1：接口帽、防脱螺钉与工具" width="420"> |
| [GLB](assets/workcells/melfi_v6/melfi_v6.glb) · [Blender](assets/workcells/melfi_v6/melfi_v6.blend) · [部件清单](assets/workcells/melfi_v6/parts.json) | [GLB](assets/workcells/rrm_tb1/rrm_tb1.glb) · [Blender](assets/workcells/rrm_tb1/rrm_tb1.blend) · [部件清单](assets/workcells/rrm_tb1/parts.json) |

| 工作位 | 任务 | 完成目标 |
| --- | --- | --- |
| MELFI V6 | 样本卡转移到盒口 | 将卡片移至指定盒口并稳定持有。 |
| MELFI V6 | 样本卡插入 | 将卡片放入指定盒内并固定，随后释放。 |
| MELFI V6 | 样本卡取出 | 将卡片完全移出指定盒口并稳定持有。 |
| MELFI V6 | 开盖 | 将指定盒盖打开至目标角度。 |
| MELFI V6 | 关盖 | 将指定盒盖关闭并锁定。 |
| RRM TB1 | FDV1 拆帽归存 | 旋松、退出接口帽并固定到归存座。 |
| RRM TB1 | 指定 SMA 拆帽归存 | 选择指定接口帽，拆卸后固定到归存座。 |
| RRM TB1 | 防脱螺钉旋松 | 达到旋松位置，同时保持螺钉防脱。 |
| RRM TB1 | 防脱螺钉旋紧 | 将螺钉旋紧到位并退出工具。 |

```bash
astrobench workcells --output workcells.json
astrobench workcell-check-assets assets/workcells --output asset-check.json
astrobench workcell-plan --workcell all --repeats 10 --seed 42 --output workcell-plan.json
```

[📖 任务、场景接入与评分](docs/workcells.zh-CN.md) · [📖 English guide](docs/workcells.md) · [🎬 FDV1](docs/media/fdv1.mp4) · [🎬 SMA](docs/media/sma.mp4) · [🎬 防脱螺钉](docs/media/captive.mp4)

硬件外形与流程参考 NASA / ESA 资料，资料链接与建模说明见[工作位指南](docs/workcells.zh-CN.md)。

## 🧰 物体集合

默认 **20 类**，可选 **Objaverse 扩展集：8,414 个物体**。扩展集包含工具、容器、便携电子设备、机械零件和舱内用品，覆盖 51 个 LVIS 类别标签及未标注物体。

清单保留物体 ID、名称、类别标签、来源链接和作者信息。使用以下命令选择物体集。

```bash
astrobench objects --output core20.json
astrobench objects --object-set objaverse8414 --output objaverse8414.json
```

[📖 Object catalog & selection](docs/objects.md) · [📖 物体集与筛选](docs/objects.zh-CN.md)

## 🛰️ 舱内场景

| ID | Cabin |
| --- | --- |
| `iss_jpm` | Kibo / JPM |
| `iss_us_lab` | US Laboratory |
| `iss_eu_lab` | European Laboratory |
| `iss_node2` | Node 2 |
| `iss_cupola` | Node 3 workcell near Cupola |

每种舱内背景可复用静态、动态抓取。MELFI 与 RRM 通过独立的[工作位任务入口](docs/workcells.zh-CN.md)选择，并按任务布局安装硬件。

```bash
astrobench scenes --output scenes.json
```

## 📏 协议工具

示例清单展示资产接口。自己的资产清单需填写 object_id、asset_sha256、geometry_group 和 split；测量字段见协议文档。

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

## 🎬 资源

| Dynamic spool | Dynamic wrench | Static spool |
| :---: | :---: | :---: |
| [![Spool](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Wrench](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Spool](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

[Objaverse](https://objaverse.allenai.org/) · [NASA Astrobee ISS assets](https://github.com/nasa/astrobee_media/tree/master/astrobee_iss) · [Space Robotics Bench](https://arxiv.org/abs/2509.23328)

## 📚 引用

如果您在研究中使用 AstroBench，可使用以下 BibTeX 引用：

```bibtex
@misc{astrouplab2026astrobench,
  author       = {{AstroUpLab}},
  title        = {{AstroBench}: Free-floating Manipulation Benchmark},
  year         = {2026},
  howpublished = {GitHub repository},
  url          = {https://github.com/AstroUpLab/AstroBench}
}
```

引用本版本时请记录仓库地址和提交编号。
