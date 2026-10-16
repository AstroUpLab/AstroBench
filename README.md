<div align="center">

# 🚀 AstroBench

### Free-floating Manipulation Benchmark

**Capture a moving object. Keep it secure after contact.**

[🌐 Website](https://astroup.com/astrobench/) · [📖 Specification](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Videos](https://astroup.com/astrobench/#videos) · [🐛 Issues](https://github.com/Brickkkkkk/AstroBench/issues)

**English** | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![Protocol tests](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Protocol](https://img.shields.io/badge/Protocol-0.1_draft-orange)](docs/protocol.md)
[![Documentation](https://img.shields.io/badge/Docs-English_%7C_中文-12345F)](https://astroup.com/astrobench/docs/current/index.html)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="A fixed-base robot arm approaching a free-floating spool inside a cabin. Click to watch recordings." width="760"></a>

*Watch the target move, the fingers make contact, and the grasp hold—or slip.*

</div>

## 🪐 What is AstroBench?

AstroBench studies manipulation of **free-floating objects with a fixed-base robot arm** inside a zero-gravity cabin. Without a supporting surface, the first touch can push a target away or set it rotating. Gripper closure alone is not enough: the object must remain securely grasped.

The benchmark separates **capture**—establishing a stable grasp—from **terminal retention**—keeping it through the end of an episode. Its broader task design also covers cabin mechanisms, insertion, reorientation and stowage.

This repository contains the **portable evaluation protocol**: deterministic episode plans, trace scoring and complete result accounting. It runs on a CPU with Python's standard library. An environment adapter supplies the measured trajectories; the full environment and pretrained policies are not included in this package.

### ✨ Highlights

- **Contact and retention:** score target-specific bilateral contact, measured closure, relative motion and continuous hold.
- **Reproducible plans:** bind object identity, geometry groups, motion conditions and protocol settings to episode hashes.
- **Explicit coverage:** keep task failures, runtime errors and missing episodes distinct; withhold a full macro score for incomplete plans.
- **Two-view recordings:** explore 40 selected examples across 20 object types, with external and cabin views.
- **Multilingual README:** English, Chinese, Japanese, Korean, Spanish, French and German guides; the full technical specification is available in English and Chinese.

## 🧭 Contents

- [🎬 Watch the tasks](#watch)
- [⚡ Quick start](#quickstart)
- [📏 How evaluation works](#evaluation)
- [🧩 Task design](#tasks)
- [📊 Development evidence](#evidence)
- [🗂️ Repository layout](#layout)
- [🛠️ Release roadmap](#roadmap)
- [🤝 Contributing and citing](#contributing)

<a id="watch"></a>

## 🎬 Watch the tasks

| Moving spool | Moving wrench | Initially static spool |
| :---: | :---: | :---: |
| [![Moving spool](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Moving wrench](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Static spool](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

**[Open the interactive gallery →](https://astroup.com/astrobench/#videos)** to search objects, switch cameras and inspect motion records.

The gallery contains **20 object types · 40 selected episodes · 80 videos**. These are selected examples, not a test-set success rate. Historical hold labels belong to the recording version; they are separate from the current terminal-retention scorer.

<a id="quickstart"></a>

## ⚡ Quick start

**Requirements:** Python 3.11+, no GPU, no runtime dependencies beyond the standard library. Commands below use a POSIX shell.

### 1. Install and check

```bash
git clone https://github.com/Brickkkkkk/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

### 2. Generate an episode plan

```bash
astrobench plan examples/catalog.json --seed 42 --output plan.json
python -c 'import json; print(json.load(open("plan.json"))["episodes"][0]["episode_id"])'
```

The bundled catalog is **synthetic interface-test input**, with no associated physical assets. For an experiment, supply verified assets with `object_id`, `asset_sha256`, `geometry_group` and `split`. The planner rejects asset or geometry-group leakage across splits.

### 3. Score a measured trajectory

Export `trace.json` from your environment adapter, then replace `EPISODE_ID` with the identifier printed above:

```bash
astrobench score plan.json EPISODE_ID trace.json --output episode-result.json
```

The trace envelope contains `episode_id`, `spec_hash` and `samples`. Samples record timestamps, per-finger target forces, measured closure, forbidden contact, escape, relative velocities and relative pose. See the [exact field contract](docs/protocol.md#trace-and-adapter-contract).

### 4. Aggregate results

```bash
python -c 'import json; json.dump([json.load(open("episode-result.json"))], open("results.json", "w"))'
astrobench report plan.json results.json --output report.json
```

This example wraps **one** episode result. A multi-episode plan will correctly report incomplete coverage. For a full report, include every planned result for one policy/checkpoint in the JSON array. CLI outputs refuse to overwrite existing files; use fresh paths for new runs.

<a id="evaluation"></a>

## 📏 How evaluation works

```text
Verified asset catalog
        ↓
Registered episode plan + identity hashes
        ↓
Environment adapter → measured trajectory
        ↓
Capture / terminal-retention judge
        ↓
Per-episode results → success, coverage and uncertainty
```

The public draft is `astrobench.capture-retain/0.1-draft`:

| Setting | Value |
| --- | --- |
| Episode horizon | 12 s |
| Continuous hold window | 1.0 s of elapsed timestamp duration |
| Nominal measurement rate / maximum gap | 50 Hz / 25 ms |
| Target contact force | At least 0.5 N per finger |
| Maximum relative linear / angular speed | 0.02 m/s / 0.2 rad/s |
| Maximum relative position / orientation excursion | 0.01 m / 0.1 rad |

**Early capture followed by loss does not pass.** Success requires a continuous valid hold window ending at the episode horizon. Invalid or truncated logs are rejected. A normal task timeout is a task failure; runtime errors and missing episodes are reported separately.

The planner offers `static`, `drift`, `tumble` and `fast_tumble` tracks. These are draft motion settings, not a frozen generalization benchmark. Thresholds still require calibration with the environment adapter. The scorer checks logs; the adapter must verify physical configuration and sensor mapping.

📖 **[Full specification](https://astroup.com/astrobench/docs/current/index.html)** · **[Protocol reference](docs/protocol.md)**

<a id="tasks"></a>

## 🧩 Task design

| Category | Families | Completion evidence |
| --- | --- | --- |
| Free-floating grasping | Capture and retain an object | Bilateral contact, actual closure and retention |
| Mechanism interaction | Doors, drawers, buttons, knobs/valves, levers | Joint state or travel, direction and ordered stages |
| Precision mating | Peg insertion, plugs, module seating | Alignment, insertion depth and seating |
| Object manipulation | Reorientation, stow and close | Target pose or ordered placement, release and closure |

The **11-family design** is broader than the current grasping recordings and public grasp judge. Other families need separate validation and task-specific judges. Formal object and motion splits remain to be frozen.

<a id="evidence"></a>

## 📊 Development evidence

A matched **40-episode cube pilot** compares a frozen ACT checkpoint with an adapted state-feedback reference: ten development positions, two motion conditions, two methods, with no retraining.

| Method | Initial condition | Acquired a grasp | Retained at horizon |
| --- | --- | ---: | ---: |
| ACT | Static | 8 / 10 | 3 / 10 |
| ACT | Moving | 6 / 10 | 0 / 10 |
| State-feedback reference | Static | 8 / 10 | 8 / 10 |
| State-feedback reference | Moving | 0 / 10 | 0 / 10 |

This pilot uses its own **15 Hz, 20-second native protocol**, not the public 12-second scorer. The reference uses privileged state, all its moving episodes hit a controller-specific tracking guard, and its static grasps occur later, leaving less time to observe retention. These results are development diagnostics—not an equal-information ranking or a 20-object generalization score.

See [pilot setup, confidence intervals and interpretation](https://astroup.com/astrobench/docs/current/index.html#pilot).

<a id="layout"></a>

## 🗂️ Repository layout

```text
AstroBench/
├── astrobench/           # Episode plans, scoring, aggregation and CLI
├── docs/protocol.md      # Trace format and adapter responsibilities
├── examples/catalog.json # Synthetic catalog for interface checks
├── tests/               # Protocol and statistics tests
├── .github/workflows/   # CI
├── README.md            # English
└── README.*.md          # Translations: zh-CN, ja, ko, es, fr, de
```

<a id="roadmap"></a>

## 🛠️ Release roadmap

- [x] Portable planning, scoring and reporting package
- [x] Protocol tests and GitHub Actions CI
- [x] Bilingual release page and technical specification
- [x] Selected grasping recordings with two camera views
- [x] Matched cube development pilot
- [ ] Portable full environment and asset distribution
- [ ] Frozen object splits and calibrated motion tracks
- [ ] Broader baseline evaluation and equal-duration retention tests
- [ ] Paper release

Automatic data collection, demonstration/teacher policies, training pipelines and raw datasets are outside this repository's release scope.

<a id="contributing"></a>

## 🤝 Contributing and citing

Found a scoring edge case or an unclear interface? [Open an issue](https://github.com/Brickkkkkk/AstroBench/issues) with the protocol version, a minimal reproducible trace and the expected result. For changes to thresholds or time semantics, explain how existing results should be versioned. Run the tests before submitting a pull request.

The paper is being revised and has no arXiv identifier yet. Until a formal citation is available, reference the repository URL and the exact commit and protocol version used in your work.

Related work: [Space Robotics Bench](https://arxiv.org/abs/2509.23328).
