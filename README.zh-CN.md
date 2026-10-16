<div align="center">

# 🚀 AstroBench

### 太空自由漂浮操作基准

**抓住运动目标，并在接触后持续保持。**

[🌐 发布页](https://astroup.com/astrobench/zh.html) · [📖 技术说明](https://astroup.com/astrobench/docs/current/zh.html) · [🎬 任务录像](https://astroup.com/astrobench/zh.html#videos) · [🐛 问题反馈](https://github.com/Brickkkkkk/AstroBench/issues)

[English](README.md) | **简体中文** | [日本語](README.ja.md) | [한국어](README.ko.md) | [Español](README.es.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

[![协议测试](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![协议版本](https://img.shields.io/badge/Protocol-0.1_draft-orange)](docs/protocol.md)
[![技术说明](https://img.shields.io/badge/Docs-English_%7C_中文-12345F)](https://astroup.com/astrobench/docs/current/zh.html)

<a href="https://astroup.com/astrobench/zh.html#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="固定基座机械臂接近舱内自由漂浮的线轴，点击观看录像。" width="760"></a>

*从目标运动、首次接触，到抓持保持或滑脱，观察完整过程。*

</div>

## 🪐 AstroBench 是什么？

AstroBench 研究**固定基座机械臂对零重力舱内自由漂浮物体的操作**。目标没有支撑，首次碰触可能将其推远或使其转动。夹爪闭合后，物体仍可能滑移或脱离。

因此，评测分别记录**捕获**——建立稳定抓持，以及**终态保持**——持续抓持到回合结束。更广的任务设计还覆盖舱内机构交互、插接、物体定向与收纳。

本仓库提供**可迁移评测协议**：确定性回合清单、轨迹评分与完整结果汇总。协议包只依赖 Python 标准库，可在 CPU 上运行。实测轨迹由环境适配器提供，当前包不包含完整环境或预训练策略。

### ✨ 主要内容

- **接触与保持判据：**核验目标专属双侧接触、实际闭合、相对运动及连续保持。
- **可复核回合清单：**将物体身份、几何分组、运动条件及协议配置绑定到回合哈希。
- **完整统计：**分别保留任务失败、运行错误和缺失回合；计划未完成时不输出完整宏平均。
- **双视角录像：**20 类物体、40 个精选样例，可切换外部与舱内视角。
- **七种语言 README：**提供英语、中文、日语、韩语、西班牙语、法语和德语版本；完整技术说明提供中英文版。

## 🧭 目录

- [🎬 任务录像](#watch)
- [⚡ 快速开始](#quickstart)
- [📏 评测方法](#evaluation)
- [🧩 任务设计](#tasks)
- [📊 开发实验](#evidence)
- [🗂️ 仓库结构](#layout)
- [🛠️ 发布进度](#roadmap)
- [🤝 参与贡献与引用](#contributing)

<a id="watch"></a>

## 🎬 任务录像

| 动态线轴 | 动态扳手 | 静态初始线轴 |
| :---: | :---: | :---: |
| [![动态线轴](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![动态扳手](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![静态初始线轴](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

**[打开交互录像集 →](https://astroup.com/astrobench/zh.html#videos)** 搜索物体、切换视角并查看运动记录。

录像集包含 **20 类物体 · 40 个精选回合 · 80 段视频**。精选样例不代表测试集成功率。历史保持标签对应录像生成时的版本，与当前终态保持评分器分开解释。

<a id="quickstart"></a>

## ⚡ 快速开始

**运行要求：**Python 3.11+，无需 GPU，运行时仅依赖标准库。以下命令使用 POSIX shell。

### 1. 安装并检查

```bash
git clone https://github.com/Brickkkkkk/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

### 2. 生成回合清单

```bash
astrobench plan examples/catalog.json --seed 42 --output plan.json
python -c 'import json; print(json.load(open("plan.json"))["episodes"][0]["episode_id"])'
```

附带目录为**接口测试用合成输入**，不对应实际物理资产。正式实验需提供已验证资产，包含 `object_id`、`asset_sha256`、`geometry_group`、`split`。清单生成器会拒绝资产或同源几何组跨划分泄漏。

### 3. 为实测轨迹评分

通过环境适配器导出 `trace.json`，将 `EPISODE_ID` 替换为上一步打印的标识：

```bash
astrobench score plan.json EPISODE_ID trace.json --output episode-result.json
```

轨迹外层包含 `episode_id`、`spec_hash` 和 `samples`。逐样本记录时间戳、每指目标接触力、实际闭合、禁止接触、越界、相对速度及相对位姿。详见[完整字段约定](https://astroup.com/astrobench/docs/current/zh.html#trace)。

### 4. 汇总结果

```bash
python -c 'import json; json.dump([json.load(open("episode-result.json"))], open("results.json", "w"))'
astrobench report plan.json results.json --output report.json
```

此例只封装**一个**回合结果，多回合计划会正确显示覆盖未完成。完整报告需在 JSON 数组中纳入同一策略／检查点的全部计划结果。CLI 不覆盖已有输出文件，新运行应使用新路径。

<a id="evaluation"></a>

## 📏 评测方法

```text
已核验的资产目录
       ↓
预登记回合清单与身份哈希
       ↓
环境适配器 → 实测轨迹
       ↓
捕获／终态保持评分器
       ↓
逐回合结果 → 成功率、覆盖与不确定性
```

公开草案版本为 `astrobench.capture-retain/0.1-draft`：

| 配置 | 数值 |
| --- | --- |
| 回合时限 | 12 s |
| 连续保持窗口 | 按时间戳累计 1.0 s |
| 名义测量频率／最大采样间隙 | 50 Hz／25 ms |
| 目标接触力 | 每指不低于 0.5 N |
| 相对线速度／角速度上限 | 0.02 m/s／0.2 rad/s |
| 相对位置／姿态漂移上限 | 0.01 m／0.1 rad |

**早期抓住、随后失抓不算成功。**成功要求连续有效保持窗口持续到回合终点。无效或截断日志会被拒绝；正常任务超时计失败，运行错误和缺失回合另外报告。

清单生成器提供 `static`、`drift`、`tumble`、`fast_tumble` 四种运动条件，属于草案配置，尚不是冻结的泛化测试集。阈值仍需结合环境适配器校准。评分器检查日志，物理配置与传感器映射由适配器核验。

📖 **[完整技术说明](https://astroup.com/astrobench/docs/current/zh.html)** · **[仓库协议参考](docs/protocol.md)**

<a id="tasks"></a>

## 🧩 任务设计

| 类别 | 任务族 | 完成证据 |
| --- | --- | --- |
| 自由漂浮抓取 | 捕获并持续抓持物体 | 双侧接触、实际闭合与保持 |
| 机构交互 | 柜门、抽屉、按钮、旋钮／阀门、拨杆 | 关节状态或行程、方向与阶段顺序 |
| 精细接合 | 插销入孔、插头插拔、模块就位 | 对齐、插入深度与就位 |
| 物体操作 | 物体定向、收纳并关闭 | 目标位姿或依次置入、释放和关闭 |

**11 个任务族**是整体设计范围，比现有抓取录像与公开抓取评分器更广。其他任务仍需独立验收和对应评分器，正式物体与运动划分尚未冻结。

<a id="evidence"></a>

## 📊 开发实验

已完成 **40 回合魔方匹配对照**：冻结 ACT 检查点与适配后的状态反馈参照，在十个开发位置、两种运动条件下评测，没有重新训练。

| 方法 | 初始条件 | 曾经抓稳 | 终态保持 |
| --- | --- | ---: | ---: |
| ACT | 静止 | 8 / 10 | 3 / 10 |
| ACT | 运动 | 6 / 10 | 0 / 10 |
| 状态反馈参照 | 静止 | 8 / 10 | 8 / 10 |
| 状态反馈参照 | 运动 | 0 / 10 | 0 / 10 |

实验使用独立的 **15 Hz、20 秒原生协议**，并非公开的 12 秒评分器。状态参照使用特权信息，其运动回合全部触发控制器自身的跟踪范围限制；静止组抓稳较晚，后续观察保持的时间也更短。因此，这些结果用于开发诊断，不构成同信息条件排名或 20 物体泛化成绩。

详见[实验设置、置信区间与结果解释](https://astroup.com/astrobench/docs/current/zh.html#pilot)。

<a id="layout"></a>

## 🗂️ 仓库结构

```text
AstroBench/
├── astrobench/           # 回合清单、评分、汇总与命令行
├── docs/protocol.md      # 轨迹格式与适配器职责
├── examples/catalog.json # 接口检查用合成目录
├── tests/               # 协议与统计测试
├── .github/workflows/   # 持续集成
├── README.md            # English
└── README.*.md          # 中文、日语、韩语、西班牙语、法语、德语
```

<a id="roadmap"></a>

## 🛠️ 发布进度

- [x] 可迁移的计划生成、评分与汇总包
- [x] 协议测试与 GitHub Actions CI
- [x] 中英文发布页与技术说明
- [x] 双视角精选抓取录像
- [x] 魔方匹配开发实验
- [ ] 完整运行环境迁移与资产分发
- [ ] 正式物体划分与运动条件校准
- [ ] 更广的基线评测与等长保持观察
- [ ] 论文发布

自动数采、示范／教师策略、训练流水线与原始数据集不在本仓库发布范围内。

<a id="contributing"></a>

## 🤝 参与贡献与引用

发现评分边界问题或接口说明不清楚，可以[提交 Issue](https://github.com/Brickkkkkk/AstroBench/issues)，附上协议版本、最小可复现轨迹和期望结果。修改阈值或时间语义时，请说明旧结果如何保留版本；提交 PR 前运行测试。

论文正在修订，尚无 arXiv 标识。正式引用信息发布前，可引用仓库地址，并注明实验所用的提交和协议版本。

相关工作：[Space Robotics Bench](https://arxiv.org/abs/2509.23328)。
