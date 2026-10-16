# AstroBench evaluation protocol

[发布页](https://astroup.com/astrobench/) · [基准说明](https://astroup.com/astrobench/docs/current/index.html)

自由漂浮物体操作的评测协议代码：回合清单生成、终态保持评分和结果汇总。
此包可独立安装，只使用 Python 标准库。环境运行接口仍需接入对应轨迹导出。

## 安装与使用

Python 3.11+：

```bash
python -m pip install .
python -m unittest discover -s tests -v
astrobench plan examples/catalog.json --seed 42 --output plan.json
astrobench score plan.json EPISODE_ID trace.json --output episode-result.json
astrobench report plan.json results.json --output report.json
```

示例 catalog 是接口测试用的合成数据；实际评测使用校验后的物体清单。
输入格式、保持判据与统计口径见 [协议文档](docs/protocol.md)。

## 目录

- `astrobench/`：回合定义、评分与命令行工具。
- `tests/`：44 项协议和统计测试。
- `examples/`：合成回合清单示例。
- `docs/`：协议使用说明。

本发布包不包含自动数采、示范策略、教师策略、训练流水线或原始数据。
评分代码消费已有轨迹，不控制机器人、不生成示范。
