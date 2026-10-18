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

각 선내 장면 설정은 정적·동적 파지와 10개 조작 작업군을 공유합니다.

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

인용할 때 저장소 URL과 커밋 ID를 기록하세요.
