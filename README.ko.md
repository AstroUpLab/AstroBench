<div align="center">

# 🚀 AstroBench

### 자유 부유 물체 조작 벤치마크

[🌐 Website](https://astroup.com/astrobench/) · [📖 Docs](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Videos](https://astroup.com/astrobench/#videos) · [🐛 Issues](https://github.com/AstroUpLab/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![Tests](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/AstroUpLab/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Objects](https://img.shields.io/badge/Default-20_classes-227799)](docs/objects.md)
[![Objaverse](https://img.shields.io/badge/Objaverse-8414_objects-448844)](docs/objects.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="AstroBench free-floating grasping" width="760"></a>

</div>

AstroBench는 자유 부유 물체의 포획과 유지, 선내 조작 작업을 다룹니다. 접촉으로 물체가 이동하거나 회전할 수 있으므로 에피소드 종료까지 안정적으로 유지하는지를 평가합니다.

## ⚡ 빠른 시작

물체 선택, 재현 가능한 에피소드 계획, 궤적 평가 및 결과 집계를 제공합니다. Python 3.11+와 표준 라이브러리를 사용합니다.

```bash
git clone https://github.com/AstroUpLab/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

## 🛠️ 우주 작업 공간

**MELFI V6**의 시료 카드 이동·삽입·회수와 덮개 개폐, **RRM TB1**의 FDV1 / SMA 캡 제거·보관과 이탈 방지 나사의 풀기·조이기를 제공합니다. 모델, 도구, 작업 정의와 측정 궤적의 평가 방법을 함께 제공합니다.

[📖 작업 공간 가이드 및 작업 목록](docs/workcells.md) · [🧊 MELFI 모델](assets/workcells/melfi_v6/) · [🛰️ RRM 모델](assets/workcells/rrm_tb1/) · [🎬 FDV1](docs/media/fdv1.mp4) · [🎬 SMA](docs/media/sma.mp4) · [🎬 나사](docs/media/captive.mp4)

RRM 영상은 기존 탁상 배치에서 캡과 나사 기구의 동작을 보여 줍니다.

```bash
astrobench workcells --output workcells.json
astrobench workcell-plan --workcell all --repeats 10 --seed 42 --output workcell-plan.json
```

## 💬 작업과 프롬프트

파지에는 `Capture the {object_name} and hold it securely.`를 사용하며 `static`, `drift`, `tumble`, `fast_tumble`의 네 조건을 비교합니다. 작업 공간은 9개 작업과 29개 작업·대상 조합을 제공합니다. 아래의 `{target_name}`은 실제 대상 이름으로 치환됩니다. RRM 패널은 벽에 고정하고 로봇은 패널 정면의 바닥판에 설치합니다.

| 작업 ID | 영어 프롬프트 템플릿 |
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

[📋 전체 작업·대상·영어 지시문](docs/tasks.md) · [📋 中文任务目录](docs/tasks.zh-CN.md)

## 🧰 물체 모음

기본값은 **20개 클래스**이며, **Objaverse 물체 8,414개**를 확장 목록으로 선택할 수 있습니다. 도구, 용기, 휴대용 전자기기, 기계 부품, 선내 용품으로 구성되며 LVIS 라벨 51개와 미분류 물체를 포함합니다.

목록에는 물체 ID, 이름, 분류, 출처 링크 및 저자 정보가 포함됩니다.

```bash
astrobench objects --output core20.json
astrobench objects --object-set objaverse8414 --output objaverse8414.json
```

[📖 Object catalog & selection](docs/objects.md) · [📖 物体集与筛选](docs/objects.zh-CN.md)

## 🛰️ 선내 장면

| ID | Cabin |
| --- | --- |
| `iss_jpm` | Kibo / JPM |
| `iss_us_lab` | US Laboratory |
| `iss_eu_lab` | European Laboratory |
| `iss_node2` | Node 2 |
| `iss_cupola` | Node 3 workcell near Cupola |

각 선내 배경에서 정적·동적 파지 작업을 사용할 수 있습니다. MELFI와 RRM은 별도의 [작업 공간 인터페이스](docs/workcells.md)에서 선택하고 작업 배치에 맞춰 하드웨어를 설치합니다.

```bash
astrobench scenes --output scenes.json
```

## 📏 프로토콜 도구

예제 목록은 자산 인터페이스를 보여 줍니다. 자산 목록에 object_id, asset_sha256, geometry_group, split을 입력하세요. 측정 필드는 프로토콜 문서를 참조하세요.

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

## 🎬 자료

| Dynamic spool | Dynamic wrench | Static spool |
| :---: | :---: | :---: |
| [![Spool](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Wrench](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Spool](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

[Objaverse](https://objaverse.allenai.org/) · [NASA Astrobee ISS assets](https://github.com/nasa/astrobee_media/tree/master/astrobee_iss) · [Space Robotics Bench](https://arxiv.org/abs/2509.23328)

## 📚 인용

연구에 AstroBench를 사용하신 경우 다음 BibTeX로 인용해 주세요.

```bibtex
@misc{astrouplab2026astrobench,
  author       = {{AstroUpLab}},
  title        = {{AstroBench}: Free-floating Manipulation Benchmark},
  year         = {2026},
  howpublished = {GitHub repository},
  url          = {https://github.com/AstroUpLab/AstroBench}
}
```

인용할 때 저장소 URL과 커밋 ID를 기록하세요.
