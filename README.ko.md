<div align="center">

# 🚀 AstroBench

### 자유 부유 물체 조작 벤치마크

**움직이는 물체를 잡고, 접촉 후에도 안정적으로 유지합니다.**

[🌐 프로젝트 페이지](https://astroup.com/astrobench/) · [📖 기술 명세 (영어)](https://astroup.com/astrobench/docs/current/index.html) · [🎬 영상](https://astroup.com/astrobench/#videos) · [🐛 이슈](https://github.com/Brickkkkkk/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | **한국어** | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![CI](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Protocol](https://img.shields.io/badge/Protocol-0.1_draft-orange)](docs/protocol.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="선실 안에서 자유롭게 떠다니는 스풀에 접근하는 고정 베이스 로봇 팔. 클릭하면 영상을 볼 수 있습니다." width="760"></a>

</div>

## 🪐 AstroBench란?

AstroBench는 무중력 선실에서 고정 베이스 로봇 팔로 자유 부유 물체를 조작하는 문제를 다룹니다. 지지면이 없으므로 첫 접촉이 물체를 밀어내거나 회전시킬 수 있습니다. 그리퍼를 닫는 것만으로는 충분하지 않으며 물체를 계속 잡고 있어야 합니다.

평가는 안정적인 파지를 형성하는 **포획**과 에피소드가 끝날 때까지 유지하는 **종료 시점 유지**를 구분합니다. 전체 과제 설계에는 선실 기구 조작, 삽입, 자세 변경, 수납도 포함됩니다.

이 저장소는 결정론적 에피소드 계획, 궤적 채점, 전체 결과 집계를 위한 이식 가능한 평가 프로토콜을 제공합니다. Python 표준 라이브러리만으로 CPU에서 실행됩니다. 측정 궤적은 환경 어댑터가 제공하며, 전체 실행 환경과 사전 학습 정책은 이 패키지에 포함되지 않습니다.

### ✨ 주요 특징

- **접촉과 유지:** 대상 물체에 대한 양쪽 손가락 접촉, 실제 닫힘 상태, 상대 운동, 연속 유지 여부를 평가합니다.
- **재현 가능한 계획:** 물체 ID, 형상 그룹, 운동 조건, 프로토콜 설정을 에피소드 해시로 연결합니다.
- **명확한 실행 집계:** 과제 실패, 실행 오류, 누락 에피소드를 구분하며 불완전한 계획에는 전체 매크로 평균을 제공하지 않습니다.
- **두 시점 영상:** 물체 20종의 선별된 40개 사례를 외부 및 선실 카메라로 확인할 수 있습니다.
- **7개 언어 README:** 상세 기술 명세는 영어와 중국어로 제공됩니다.

## 🧭 목차

- [🎬 과제 영상](#watch)
- [⚡ 빠른 시작](#quickstart)
- [📏 평가 방법](#evaluation)
- [🧩 과제 설계](#tasks)
- [📊 개발 실험](#evidence)
- [🗂️ 저장소 구조](#layout)
- [🛠️ 공개 진행 상황](#roadmap)
- [🤝 기여 및 인용](#contributing)

<a id="watch"></a>

## 🎬 과제 영상

| 움직이는 스풀 | 움직이는 렌치 | 초기 정지 스풀 |
| --- | --- | --- |
| [![움직이는 스풀](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![움직이는 렌치](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![초기 정지 스풀](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

[대화형 영상 모음](https://astroup.com/astrobench/#videos)에서 물체 검색, 카메라 전환, 운동 기록 확인이 가능합니다. **물체 20종 · 선별된 에피소드 40개 · 영상 80개**를 제공합니다. 선별 사례는 테스트 세트 성공률이 아닙니다. 과거 유지 라벨은 녹화 당시 판정 기준에 속하며 현재 종료 시점 유지 채점과 별도로 해석합니다.

<a id="quickstart"></a>

## ⚡ 빠른 시작

**요구 사항:** Python 3.11 이상. GPU 없이 실행되며 런타임 의존성은 표준 라이브러리뿐입니다. 아래 명령은 POSIX 셸용입니다.

### 1. 설치 및 확인

```bash
git clone https://github.com/Brickkkkkk/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

테스트는 프로토콜과 통계 처리를 검증합니다.

### 2. 에피소드 계획 생성

```bash
astrobench plan examples/catalog.json --seed 42 --output plan.json
python -c 'import json; print(json.load(open("plan.json"))["episodes"][0]["episode_id"])'
```

제공 카탈로그는 실제 물리 자산이 없는 합성 인터페이스 테스트 입력입니다. 실험에는 검증된 `object_id`, `asset_sha256`, `geometry_group`, `split`을 제공해야 합니다. 자산이나 형상 그룹이 데이터 분할을 넘나들면 계획 생성기가 거부합니다.

### 3. 측정 궤적 채점

```bash
astrobench score plan.json EPISODE_ID trace.json --output episode-result.json
```

먼저 환경 어댑터에서 `trace.json`을 내보낸 뒤 `EPISODE_ID`를 앞서 출력된 ID로 바꿉니다. 궤적 최상위 필드는 `episode_id`, `spec_hash`, `samples`입니다. 각 샘플은 타임스탬프, 손가락별 대상 접촉력, 실제 닫힘, 금지 접촉, 이탈, 상대 속도와 자세를 기록합니다. [정확한 필드 명세 (영어)](docs/protocol.md#trace-and-adapter-contract)를 참조하세요.

### 4. 결과 집계

```bash
python -c 'import json; json.dump([json.load(open("episode-result.json"))], open("results.json", "w"))'
astrobench report plan.json results.json --output report.json
```

이 예제는 한 에피소드만 배열로 묶으므로 여러 에피소드 계획에서는 미완료로 집계됩니다. 전체 보고서는 동일 정책/체크포인트의 모든 계획 결과를 배열에 포함해야 합니다. CLI는 기존 출력 파일을 덮어쓰지 않으므로 새 실행에는 새 경로를 사용하세요.

<a id="evaluation"></a>

## 📏 평가 방법

검증된 자산 카탈로그 → ID 해시가 포함된 등록 계획 → 환경 어댑터의 측정 궤적 → 포획/종료 시점 유지 판정 → 성공률, 완료 범위, 불확실성 집계. 공개 초안 버전은 `astrobench.capture-retain/0.1-draft`입니다.

| 설정 | 값 |
| --- | --- |
| 에피소드 길이 | 12 s |
| 연속 유지 구간 | 타임스탬프 기준 경과 시간 1.0 s |
| 명목 측정 주파수 / 최대 간격 | 50 Hz / 25 ms |
| 대상 접촉력 | 손가락당 최소 0.5 N |
| 최대 상대 선속도 / 각속도 | 0.02 m/s / 0.2 rad/s |
| 최대 상대 위치 / 방향 변화 | 0.01 m / 0.1 rad |

**일찍 잡았더라도 이후 놓치면 성공이 아닙니다.** 에피소드 종료까지 유효한 연속 유지 구간이 이어져야 합니다. 잘못되거나 중간에 끊긴 로그는 거부합니다. 정상적인 시간 초과는 과제 실패이며 실행 오류, 누락과 구분됩니다.

계획 생성기는 `static`, `drift`, `tumble`, `fast_tumble` 조건을 제공합니다. 이는 초안 운동 설정이며 확정된 일반화 벤치마크가 아닙니다. 임계값은 환경 어댑터와 함께 보정해야 합니다. 채점기는 로그를 검사하고 어댑터는 물리 설정과 센서 매핑을 검증합니다.

📖 [기술 명세 (영어)](https://astroup.com/astrobench/docs/current/index.html) · [Protocol reference (English)](docs/protocol.md)

<a id="tasks"></a>

## 🧩 과제 설계

| 분류 | 과제군 | 완료 증거 |
| --- | --- | --- |
| 자유 부유 파지 | 물체 포획 및 유지 | 양측 접촉, 실제 닫힘, 유지 |
| 기구 조작 | 문, 서랍, 버튼, 노브/밸브, 레버 | 관절 상태 또는 이동량, 방향, 단계 순서 |
| 정밀 결합 | 핀 삽입, 플러그, 모듈 장착 | 정렬, 삽입 깊이, 안착 |
| 물체 조작 | 자세 변경, 수납 및 닫기 | 목표 자세 또는 배치·놓기·닫기의 순서 |

11개 과제군의 설계 범위는 현재 파지 영상과 공개 파지 판정기보다 넓습니다. 다른 과제는 별도 검증과 전용 판정기가 필요합니다. 공식 물체 및 운동 분할은 아직 확정되지 않았습니다.

<a id="evidence"></a>

## 📊 개발 실험

40개 에피소드의 큐브 대응 비교에서는 고정된 ACT 체크포인트와 인터페이스에 맞게 조정한 상태 피드백 참조 제어기를 개발 위치 10개와 운동 조건 2개에서 평가했습니다. 재학습은 하지 않았습니다.

| 방법 | 초기 조건 | 파지 성립 | 종료 시점 유지 |
| --- | --- | --- | --- |
| ACT | 정지 | 8 / 10 | 3 / 10 |
| ACT | 운동 | 6 / 10 | 0 / 10 |
| 상태 피드백 참조 | 정지 | 8 / 10 | 8 / 10 |
| 상태 피드백 참조 | 운동 | 0 / 10 | 0 / 10 |

이 실험은 공개 12초 채점기와 다른 **15 Hz, 20초의 자체 프로토콜**을 사용합니다. 참조 제어기는 특권 상태 정보를 사용하며 모든 운동 에피소드가 제어기 자체 추적 범위 제한으로 종료되었습니다. 정지 조건에서는 파지가 늦게 성립해 유지 관찰 시간도 더 짧습니다. 따라서 동일 정보 조건의 순위나 물체 20종의 일반화 점수가 아닌 개발 진단 결과입니다. [설정, 신뢰구간, 해석 (영어)](https://astroup.com/astrobench/docs/current/index.html#pilot)을 참조하세요.

<a id="layout"></a>

## 🗂️ 저장소 구조

```text
AstroBench/
├── astrobench/
├── docs/protocol.md
├── examples/catalog.json
├── tests/
├── .github/workflows/
├── README.md
└── README.*.md
```

`astrobench/`는 계획·채점·집계·CLI, `docs/protocol.md`는 궤적 명세, `examples/`는 합성 카탈로그, `tests/`는 프로토콜과 통계 테스트, `.github/workflows/`는 CI, `README.*.md`는 언어별 안내입니다.

<a id="roadmap"></a>

## 🛠️ 공개 진행 상황

- [x] 이식 가능한 계획·채점·집계 패키지
- [x] 프로토콜 테스트와 GitHub Actions CI
- [x] 영어·중국어 공개 페이지 및 기술 명세, 다국어 README
- [x] 두 시점의 선별 파지 영상
- [x] 큐브 대응 개발 실험
- [ ] 전체 환경 이식과 자산 배포
- [ ] 물체 분할 확정 및 운동 조건 보정
- [ ] 더 넓은 기준 방법 평가 및 동일 관찰 시간 유지 실험
- [ ] 논문 공개

자동 데이터 수집, 시연/교사 정책, 학습 파이프라인, 원시 데이터셋은 이 저장소의 공개 범위에 포함되지 않습니다.

<a id="contributing"></a>

## 🤝 기여 및 인용

채점 경계 사례나 불명확한 인터페이스를 발견하면 프로토콜 버전, 최소 재현 궤적, 기대 결과와 함께 [이슈](https://github.com/Brickkkkkk/AstroBench/issues)를 작성하세요. 임계값이나 시간 의미를 변경할 때는 기존 결과의 버전 관리 방법을 설명하고 PR 제출 전에 테스트를 실행하세요.

논문은 수정 중이며 아직 arXiv ID가 없습니다. 정식 인용 정보가 공개되기 전에는 저장소 URL, 사용한 정확한 커밋과 프로토콜 버전을 명시하세요.

관련 연구: [Space Robotics Bench](https://arxiv.org/abs/2509.23328).

