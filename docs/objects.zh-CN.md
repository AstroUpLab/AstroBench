# 物体集合与舱内场景

## 选择物体集

默认使用 `core20`，保留原有 20 类物体及排列顺序。可选 `objaverse8414`，包含筛选保留的全部 8,414 个 Objaverse 物体实例，覆盖 51 个 LVIS 标签及未标注物体。

```bash
astrobench objects --output core20.json
astrobench objects --object-set objaverse8414 --output objaverse8414.json
```

导出文件包含集合 ID、物体数量、清单 SHA-256 和逐物体记录。Objaverse 条目保留来源 UID、名称、类别、分组、来源链接、作者、许可和筛选理由。清单随 Python 安装包分发，读取时校验解压内容的哈希与唯一 ID。每次导出使用新的文件名。

## 生成回合计划

资产清单填写 `object_id`、`asset_sha256`、`geometry_group` 和 `split`。物体 ID 与导出的清单对应；Objaverse 使用 `objaverse_<source_uid>`。

```bash
astrobench plan assets.json --seed 42 --output core20-plan.json
astrobench plan assets.json --object-set objaverse8414 --seed 42 --output expanded-plan.json
astrobench plan examples/catalog.json --object-set custom --seed 42 --output example-plan.json
```

默认选择 20 类，扩展选项选择全部 8,414 个物体，`custom` 使用传入的清单。选择器检查重复和缺失 ID，协议检查资产哈希、几何分组和数据划分。回合标识绑定所选资产与运动条件。轨迹字段、评分和汇总方式见[协议文档](protocol.md)。

## 按类别和名称筛选

主库为 Objaverse 1.0，固定版本为 `556637099bf4fa79ea7b239d0d9c328b8a2e9ac8`，共扫描 798,759 个索引物体。规则存放在 `astrobench/data/objaverse_rules.json`，来源和清单哈希记录在 `astrobench/data/objaverse_source.json`。

筛选面向刚性工具、容器、便携电子设备、机械零件、科学设备和舱内用品。名称标准化后，结合完整词匹配、类别标签和零件名称进行判断。场景、建筑、家具、整车、生物及不适合的装饰模型被过滤；名称含糊或类别冲突的条目进入复核清单。扩展集合按来源元数据选择 CC0 或 CC BY 物体，并保留逐物体作者和许可信息。

```bash
python scripts/astrobench_fetch_objaverse_metadata.py --cache outputs/objaverse_metadata --workers 6
python scripts/astrobench_filter_objaverse.py \
  --metadata outputs/objaverse_metadata/metadata \
  --lvis outputs/objaverse_metadata/lvis-annotations.json.gz \
  --rules astrobench/data/objaverse_rules.json \
  --output outputs/objaverse_selection
```

输出包括完整筛选日志、保留条目、UID 清单、类别统计、输入哈希和元数据覆盖情况。

## 舱内场景

```bash
astrobench scenes --output scenes.json
```

默认 `iss_jpm`，另外提供 `iss_us_lab`、`iss_eu_lab`、`iss_node2`、`iss_cupola`。Cupola 场景的操作区位于相邻 Node 3 舱内。场景背景采用 NASA Astrobee ISS 资产，机械臂固定安装，各舱内场景复用任务物体和初始状态。

任务布局包括 20 类物体的静态、动态抓取，以及舱门、抽屉、面板按钮、旋钮/阀门、拨杆、插销、插头、模块安装、重定向、收纳关盖十类操作。可逆操作分方向配置，共十五个操作子项。

来源：[Objaverse](https://objaverse.allenai.org/docs/objaverse-1.0/)、[固定版本元数据](https://huggingface.co/datasets/allenai/objaverse/tree/556637099bf4fa79ea7b239d0d9c328b8a2e9ac8)、[NASA ISS 资产](https://github.com/nasa/astrobee_media/tree/master/astrobee_iss)。
