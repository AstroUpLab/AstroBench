<div align="center">

# 🚀 AstroBench

### 自由浮遊物体の操作ベンチマーク

**動く物体を捕らえ、接触後も安定して保持する。**

[🌐 プロジェクトページ](https://astroup.com/astrobench/) · [📖 技術仕様（英語）](https://astroup.com/astrobench/docs/current/index.html) · [🎬 動画](https://astroup.com/astrobench/#videos) · [🐛 Issue](https://github.com/Brickkkkkk/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | **日本語** | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![CI](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Protocol](https://img.shields.io/badge/Protocol-0.1_draft-orange)](docs/protocol.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="船内を自由浮遊するスプールに接近する固定ベースのロボットアーム。クリックして動画を再生。" width="760"></a>

</div>

## 🪐 AstroBench とは？

AstroBench は、無重力の船内で固定ベースのロボットアームが自由浮遊物体を操作する課題を扱います。支持面がないため、最初の接触で物体が押し流されたり回転したりします。グリッパーを閉じるだけでは十分ではなく、物体を保持し続ける必要があります。

評価では、安定した把持を成立させる「捕獲」と、エピソード終了まで維持する「終端保持」を区別します。より広いタスク設計には、船内機構の操作、挿入、姿勢変更、収納も含まれます。

このリポジトリには、決定的なエピソード計画、軌跡の採点、結果集計を行う移植可能な評価プロトコルが含まれます。Python 標準ライブラリで CPU 上で動作します。測定軌跡は環境アダプターから供給します。完全な実行環境と事前学習済みポリシーは同梱していません。

### ✨ 主な特徴

- **接触と保持：**対象物に対する両指の接触、実測した閉鎖状態、相対運動、連続保持を評価。
- **再現可能な計画：**物体 ID、形状グループ、運動条件、プロトコル設定をエピソードのハッシュに結び付けます。
- **実行状況を明示：**タスク失敗、実行エラー、未実行エピソードを区別し、不完全な計画には全体のマクロ平均を出しません。
- **2 視点の動画：**20 種類の物体について 40 の選択例を、外部・船内カメラから確認できます。
- **7 言語の README：**詳細な技術仕様は英語・中国語で提供します。

## 🧭 目次

- [🎬 タスク動画](#watch)
- [⚡ クイックスタート](#quickstart)
- [📏 評価方法](#evaluation)
- [🧩 タスク設計](#tasks)
- [📊 開発実験](#evidence)
- [🗂️ リポジトリ構成](#layout)
- [🛠️ 公開状況](#roadmap)
- [🤝 貢献と引用](#contributing)

<a id="watch"></a>

## 🎬 タスク動画

| 移動中のスプール | 移動中のレンチ | 初期静止のスプール |
| --- | --- | --- |
| [![移動中のスプール](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![移動中のレンチ](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![初期静止のスプール](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

[インタラクティブな動画一覧](https://astroup.com/astrobench/#videos)では、物体の検索、視点の切り替え、運動記録の確認ができます。**20 種類・40 の選択エピソード・80 本の動画**を掲載しています。選択例はテストセットの成功率を表すものではありません。過去の保持ラベルは収録時の判定基準に属し、現在の終端保持スコアとは別に扱います。

<a id="quickstart"></a>

## ⚡ クイックスタート

**要件：**Python 3.11 以上。GPU は不要で、実行時依存は標準ライブラリのみです。以下は POSIX シェル用コマンドです。

### 1. インストールと確認

```bash
git clone https://github.com/Brickkkkkk/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

テストはプロトコルと統計処理を検証します。

### 2. エピソード計画の生成

```bash
astrobench plan examples/catalog.json --seed 42 --output plan.json
python -c 'import json; print(json.load(open("plan.json"))["episodes"][0]["episode_id"])'
```

付属カタログはインターフェース試験用の合成入力で、実物のアセットを含みません。実験には検証済みの `object_id`、`asset_sha256`、`geometry_group`、`split` を指定します。アセットや形状グループが異なるデータ分割にまたがる場合、計画生成は拒否されます。

### 3. 測定軌跡の採点

```bash
astrobench score plan.json EPISODE_ID trace.json --output episode-result.json
```

先に環境アダプターで `trace.json` を出力し、`EPISODE_ID` を表示された ID に置き換えます。軌跡は `episode_id`、`spec_hash`、`samples` を持ちます。各サンプルには時刻、各指の対象接触力、実測閉鎖、禁止接触、逸脱、相対速度・姿勢を記録します。[フィールド仕様（英語）](docs/protocol.md#trace-and-adapter-contract)を参照してください。

### 4. 結果の集計

```bash
python -c 'import json; json.dump([json.load(open("episode-result.json"))], open("results.json", "w"))'
astrobench report plan.json results.json --output report.json
```

この例は 1 エピソードのみを配列にするため、複数エピソードの計画では未完了として報告されます。完全な集計には同一ポリシー／チェックポイントの全計画結果を配列に含めます。CLI は既存出力を上書きしないため、新しい実行には別の出力先を使います。

<a id="evaluation"></a>

## 📏 評価方法

検証済みアセット → ID ハッシュ付き計画 → 環境アダプターの測定軌跡 → 捕獲／終端保持の判定 → 成功率、完了状況、不確実性の集計。公開草案は `astrobench.capture-retain/0.1-draft` です。

| 設定 | 値 |
| --- | --- |
| エピソード長 | 12 s |
| 連続保持窓 | タイムスタンプの経過時間で 1.0 s |
| 標準測定周波数／最大間隔 | 50 Hz / 25 ms |
| 対象接触力 | 各指 0.5 N 以上 |
| 相対並進速度／角速度の上限 | 0.02 m/s / 0.2 rad/s |
| 相対位置／姿勢変化の上限 | 0.01 m / 0.1 rad |

**早期に捕獲しても、その後失えば成功ではありません。**終了時点まで連続した有効保持窓が必要です。不正・途中で切れたログは拒否されます。通常の時間切れはタスク失敗であり、実行エラーや未実行とは別に集計します。

計画生成には `static`、`drift`、`tumble`、`fast_tumble` があり、いずれも草案の運動条件です。正式な汎化ベンチマークはまだ固定されていません。閾値は環境アダプターと校正する必要があります。採点器はログを検証し、物理設定とセンサー対応の検証はアダプターが担います。

📖 [技術仕様（英語）](https://astroup.com/astrobench/docs/current/index.html) · [Protocol reference (English)](docs/protocol.md)

<a id="tasks"></a>

## 🧩 タスク設計

| 分類 | タスク族 | 完了の根拠 |
| --- | --- | --- |
| 自由浮遊把持 | 捕獲と保持 | 両側接触、実際の閉鎖、保持 |
| 機構操作 | ドア、引き出し、ボタン、ノブ／バルブ、レバー | 関節状態・移動量、方向、段階順序 |
| 精密接合 | ペグ挿入、プラグ、モジュール装着 | 位置合わせ、挿入深さ、着座 |
| 物体操作 | 姿勢変更、収納と閉鎖 | 目標姿勢、または配置・解放・閉鎖の順序 |

11 タスク族の設計範囲は、現在の把持動画と公開把持判定器より広いものです。他のタスクには個別の検証と判定器が必要です。正式な物体・運動の分割は未確定です。

<a id="evidence"></a>

## 📊 開発実験

40 エピソードの立方体の対応比較では、凍結した ACT チェックポイントと適応済み状態フィードバック参照を、10 の開発位置と 2 運動条件で評価しました。再学習は行っていません。

| 手法 | 初期条件 | 把持成立 | 終端保持 |
| --- | --- | --- | --- |
| ACT | 静止 | 8 / 10 | 3 / 10 |
| ACT | 移動 | 6 / 10 | 0 / 10 |
| 状態フィードバック参照 | 静止 | 8 / 10 | 8 / 10 |
| 状態フィードバック参照 | 移動 | 0 / 10 | 0 / 10 |

この実験は独自の **15 Hz・20 秒のネイティブプロトコル**を使用し、公開 12 秒採点器とは異なります。参照手法は特権状態を利用し、その移動条件では全試行が制御器固有の追跡範囲制限で終了しました。静止条件では把持成立が遅く、保持を観察する時間も短くなります。同じ情報条件での順位付けや 20 物体の汎化成績ではなく、開発用の診断結果です。[設定・信頼区間・解釈（英語）](https://astroup.com/astrobench/docs/current/index.html#pilot)を参照してください。

<a id="layout"></a>

## 🗂️ リポジトリ構成

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

`astrobench/` は計画・採点・集計・CLI、`docs/protocol.md` は軌跡仕様、`examples/` は合成カタログ、`tests/` はプロトコルと統計テスト、`.github/workflows/` は CI、`README.*.md` は各言語のガイドです。

<a id="roadmap"></a>

## 🛠️ 公開状況

- [x] 移植可能な計画・採点・集計パッケージ
- [x] プロトコルテストと GitHub Actions CI
- [x] 英中の公開ページ・技術仕様と多言語 README
- [x] 2 視点の選択把持動画
- [x] 立方体の対応開発実験
- [ ] 完全な環境の移植とアセット配布
- [ ] 物体分割の固定と運動条件の校正
- [ ] 基準手法の拡充と同一観察時間の保持試験
- [ ] 論文公開

自動データ収集、デモ／教師ポリシー、学習パイプライン、生データセットは公開対象外です。

<a id="contributing"></a>

## 🤝 貢献と引用

判定の境界ケースや不明瞭なインターフェースを見つけた場合は、プロトコル版、最小再現軌跡、期待結果を添えて [Issue](https://github.com/Brickkkkkk/AstroBench/issues) を作成してください。閾値や時間の意味を変更する際は、既存結果の版管理も説明し、PR 前にテストを実行してください。

論文は改訂中で arXiv ID はまだありません。正式な引用情報が公開されるまでは、リポジトリ URL と使用したコミット・プロトコル版を明記してください。

関連研究： [Space Robotics Bench](https://arxiv.org/abs/2509.23328).

