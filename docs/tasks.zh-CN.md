# 任务与 Prompt 目录

[English](tasks.md) · [简体中文](tasks.zh-CN.md) · [README](../README.zh-CN.md)

AstroBench 包含自由漂浮捕获与保持任务的四个运动轨道、5 项 MELFI 任务和 4 项 RRM 任务。工作位任务展开后共 **29 个任务与目标组合**：三个 MELFI 盒对应 15 个组合，FDV1、九个 SMA 位置和两个防脱螺钉对应 14 个组合。本页列出全部公开任务及其英文指令。

## 导出全部指令

版本化语言注册表位于 [task_prompts.json](../astrobench/data/task_prompts.json)。可将展开后的指令导出，用于策略输入或实验记录：

```bash
# Default: 20 objects x 4 tracks + 29 workcell targets = 109 instructions
astrobench task-prompts --output task-prompts.json

# Every concrete MELFI / RRM instruction
astrobench task-prompts --scope workcells --output workcell-prompts.json

# Expanded object instructions, including all four capture tracks
astrobench task-prompts --object-set objaverse8414 --scope capture --output objaverse-prompts.json
```

`--object-set all` 导出两个物体集；`--scope capture` 选择抓取指令，`--scope workcells` 选择 29 个工作位指令，`--scope all` 合并两部分。同一任务在不同重复回合与抓取轨道中保持指令一致，便于比较运动条件变化的影响。

## 自由漂浮捕获与保持

**任务 ID：** `capture_retain`  
**指令模板：** `Capture the {object_name} and hold it securely.`

捕获指定自由漂浮物体，并保持至回合结束。成功要求最后一秒内维持稳定的双侧接触、实际夹爪闭合及受控的相对运动。回合时长为 12 秒，测量字段与阈值见[抓取协议](protocol.md)。

### 四个运动轨道

| 轨道 | 初始线速度 | 初始角速度 | 条件 |
| --- | --- | --- | --- |
| `static` | 0 m/s | 0 rad/s | 初始静止 |
| `drift` | 0.02 m/s | 0 rad/s | 仅有初始漂移 |
| `tumble` | 0.02 m/s | 0.5 rad/s | 初始漂移与转动 |
| `fast_tumble` | 0.05 m/s | 1.0 rad/s | 更快的初始漂移与转动 |

种子与物体 ID 决定世界坐标系 X 轴线速度和 Z 轴角速度的正负方向；速度仅在重置时施加一次。每个种子的默认计划包含 **80 个物体与轨道组合**。物体位姿、机械臂位姿和相机配置由环境设置定义。

### 默认 20 类物体的英文指令

每一行均适用于四个轨道。英文物体名称沿用既有措辞，`l bracket` 与 `t fitting` 也保持原样。

| 物体 ID | 英文名称 | 英文 Prompt |
| --- | --- | --- |
| `candidate_standard_cube` | standard cube | Capture the standard cube and hold it securely. |
| `candidate_rectangular_block` | rectangular block | Capture the rectangular block and hold it securely. |
| `candidate_cylindrical_part` | cylindrical part | Capture the cylindrical part and hold it securely. |
| `candidate_spherical_part` | spherical part | Capture the spherical part and hold it securely. |
| `candidate_sample_tube` | sample tube | Capture the sample tube and hold it securely. |
| `candidate_sealed_bottle` | sealed bottle | Capture the sealed bottle and hold it securely. |
| `candidate_round_can` | round can | Capture the round can and hold it securely. |
| `candidate_lidded_box` | lidded box | Capture the lidded box and hold it securely. |
| `candidate_screwdriver` | screwdriver | Capture the screwdriver and hold it securely. |
| `candidate_wrench` | wrench | Capture the wrench and hold it securely. |
| `candidate_pliers` | pliers | Capture the pliers and hold it securely. |
| `candidate_small_hammer` | small hammer | Capture the small hammer and hold it securely. |
| `candidate_flashlight` | flashlight | Capture the flashlight and hold it securely. |
| `candidate_battery_pack` | battery pack | Capture the battery pack and hold it securely. |
| `candidate_handheld_terminal` | handheld terminal | Capture the handheld terminal and hold it securely. |
| `candidate_small_camera` | small camera | Capture the small camera and hold it securely. |
| `candidate_ring_part` | ring part | Capture the ring part and hold it securely. |
| `candidate_spool` | spool | Capture the spool and hold it securely. |
| `candidate_l_bracket` | l bracket | Capture the l bracket and hold it securely. |
| `candidate_t_fitting` | t fitting | Capture the t fitting and hold it securely. |

### Objaverse 扩展集

选择 `objaverse8414` 即使用 **8,414 个物体的清单**。每条记录的来源名称经空白规范化后，填入同一个抓取模板。名称保留原始含义，可能包含产品名称或非英文文字；物体身份由 `object_id` 与资产清单确定，相近名称不会合并不同物体。

仅抓取指令的导出文件包含 **33,656 条物体与轨道记录**。使用导出文件即可获取完整列表，无需在本页重复数千行。名称、类别标签、署名信息和筛选规则见[物体集指南](objects.zh-CN.md)。

自定义抓取资产清单可通过 `object_name` 指定指令中的名称；未提供时使用将下划线替换为空格后的物体 ID。默认物体集与 Objaverse 使用各自注册的名称。

## 工作位英文指令模板

将 `{target_name}` 替换为下表中的准确目标名。指令描述任务完成目标，初始几何、状态阈值和末态保持时间见[工作位协议](workcells.zh-CN.md)。

| 任务 ID | 英文 Prompt 模板 |
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

## MELFI V6：全部 15 个任务与目标指令

目标 ID 对应托盘上的三个盒子，不随相机画面左右位置变化：

| 目标 ID | 指令中的目标名 |
| --- | --- |
| `Front_quarter_box` | front quarter box |
| `Middle_quarter_box` | middle quarter box |
| `Rear_half_box` | rear half box |

卡片转移要求将卡片保持在盒口；插入要求将卡片释放并固定在盒内；取出要求将卡片保持在完全离开盒口的位置。开盖与关盖分别对应独立任务及初态。

| 任务 ID | 目标 ID | 英文 Prompt |
| --- | --- | --- |
| `card_transfer_to_mouth` | `Front_quarter_box` | Move the card to the opening of the front quarter box and hold it aligned. |
| `card_transfer_to_mouth` | `Middle_quarter_box` | Move the card to the opening of the middle quarter box and hold it aligned. |
| `card_transfer_to_mouth` | `Rear_half_box` | Move the card to the opening of the rear half box and hold it aligned. |
| `card_insert` | `Front_quarter_box` | Insert the card fully into the front quarter box, release it, and leave it retained inside. |
| `card_insert` | `Middle_quarter_box` | Insert the card fully into the middle quarter box, release it, and leave it retained inside. |
| `card_insert` | `Rear_half_box` | Insert the card fully into the rear half box, release it, and leave it retained inside. |
| `card_extract` | `Front_quarter_box` | Remove the card from the front quarter box and hold it clear of the opening. |
| `card_extract` | `Middle_quarter_box` | Remove the card from the middle quarter box and hold it clear of the opening. |
| `card_extract` | `Rear_half_box` | Remove the card from the rear half box and hold it clear of the opening. |
| `lid_open` | `Front_quarter_box` | Open the lid of the front quarter box and leave it open. |
| `lid_open` | `Middle_quarter_box` | Open the lid of the middle quarter box and leave it open. |
| `lid_open` | `Rear_half_box` | Open the lid of the rear half box and leave it open. |
| `lid_close` | `Front_quarter_box` | Close and latch the lid of the front quarter box, then withdraw the gripper. |
| `lid_close` | `Middle_quarter_box` | Close and latch the lid of the middle quarter box, then withdraw the gripper. |
| `lid_close` | `Rear_half_box` | Close and latch the lid of the rear half box, then withdraw the gripper. |

## RRM TB1：全部 14 个任务与目标指令

面板采用壁挂布局，机械臂位于正前方地面底板上，安装关系见[工作位指南](workcells.zh-CN.md#rrm-tb1)。FDV1 使用多功能工具 MFT 与第三级帽适配器 TCA；SMA 使用安全帽工具 SCT 与 SMA 适配器；防脱螺钉使用 SCT 与 #10 Torque Set 适配器。

`SMA_r_c` 表示阵列中的实际位置：行号沿面板局部 +Y 方向递增，列号沿 +X 方向递增；在 r003 壁挂布局中，面板局部 +Y 映射到世界 +Z，因此第 1 行在下、第 3 行在上；正对面板时，第 1 至第 3 列从左向右排列。移动相机不会改变目标编号。`captive_1` 与 `captive_2` 对应两个独立螺钉位置。默认活动 SMA 目标为 `SMA_2_2`，默认活动防脱螺钉为 `captive_1`；其它目标的重建和同一计划下的评分方式见工作位指南。

| 任务 ID | 目标 ID | 英文 Prompt |
| --- | --- | --- |
| `fdv1_remove_stow` | `FDV1` | Unscrew and remove the FDV1 cap, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `sma_remove_stow` | `SMA_1_1` | Unscrew and remove the SMA cap at row 1, column 1, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `sma_remove_stow` | `SMA_1_2` | Unscrew and remove the SMA cap at row 1, column 2, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `sma_remove_stow` | `SMA_1_3` | Unscrew and remove the SMA cap at row 1, column 3, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `sma_remove_stow` | `SMA_2_1` | Unscrew and remove the SMA cap at row 2, column 1, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `sma_remove_stow` | `SMA_2_2` | Unscrew and remove the SMA cap at row 2, column 2, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `sma_remove_stow` | `SMA_2_3` | Unscrew and remove the SMA cap at row 2, column 3, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `sma_remove_stow` | `SMA_3_1` | Unscrew and remove the SMA cap at row 3, column 1, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `sma_remove_stow` | `SMA_3_2` | Unscrew and remove the SMA cap at row 3, column 2, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `sma_remove_stow` | `SMA_3_3` | Unscrew and remove the SMA cap at row 3, column 3, retain it in its adapter, dock the adapter in its stowage holder, and withdraw the driver. |
| `captive_loosen` | `captive_1` | Loosen the captive screw 1 without releasing it from the panel and hold it in the loosened position. |
| `captive_loosen` | `captive_2` | Loosen the captive screw 2 without releasing it from the panel and hold it in the loosened position. |
| `captive_tighten` | `captive_1` | Tighten the captive screw 1 until it is seated, keep it captive, and withdraw the driver. |
| `captive_tighten` | `captive_2` | Tighten the captive screw 2 until it is seated, keep it captive, and withdraw the driver. |

拆帽任务包括将帽保持在适配器内、将适配器与帽一同归存，再退出驱动工具。防脱螺钉在旋松和旋紧过程中始终保持在面板上。

## 选择并记录任务

```bash
astrobench plan assets.json --seed 42 --output capture-plan.json
astrobench workcell-plan --workcell all --repeats 10 --seed 42 \
  --asset-root assets/workcells --output workcell-plan.json

# Select one task and one concrete target
astrobench workcell-plan --workcell rrm_tb1 --task sma_remove_stow --target SMA_1_3 \
  --repeats 10 --seed 42 --output sma-1-3-plan.json
```

工作位计划按任务与目标展开，全部 29 个组合各重复 10 次得到 290 个回合。将 `episode["spec"]["language_prompt"]["text"]` 连同所选场景和目标传给策略。绑定信息包含语言注册表版本与 SHA-256、目标身份和指令文本 SHA-256，回合 `spec_hash` 覆盖全部字段。保留计划、轨迹和结果的身份字段用于汇总。完整接入和评分命令见[工作位指南](workcells.zh-CN.md)。
