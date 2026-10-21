# Tasks and prompts

[English](tasks.md) · [简体中文](tasks.zh-CN.md) · [README](../README.md)

AstroBench has one free-floating capture-and-retain task with four motion tracks, five MELFI tasks and four RRM tasks. The workcell tasks expand to **29 task–target combinations**: 15 for three MELFI boxes, and 14 for FDV1, nine SMA positions and two captive screws. This page lists every public task and its English instruction.

## Export the instructions

The versioned language registry is [task_prompts.json](../astrobench/data/task_prompts.json). Export resolved instructions for a policy or experiment log:

```bash
# Default: 20 objects x 4 tracks + 29 workcell targets = 109 instructions
astrobench task-prompts --output task-prompts.json

# Every concrete MELFI / RRM instruction
astrobench task-prompts --scope workcells --output workcell-prompts.json

# Expanded object instructions, including all four capture tracks
astrobench task-prompts --object-set objaverse8414 --scope capture --output objaverse-prompts.json
```

`--object-set all` exports both object inventories. `--scope capture` selects grasping instructions; `--scope workcells` selects the 29 workcell instructions; `--scope all` combines them. The wording stays the same across repeats and capture tracks so that changes in motion can be compared under the same instruction.

## Free-floating capture and retention

**Task ID:** `capture_retain`  
**Template:** `Capture the {object_name} and hold it securely.`

Capture the selected free-floating object and retain it until the end of the episode. Success requires stable bilateral contact, actual gripper closure and bounded relative motion during the final second. The horizon is 12 seconds; see the [capture protocol](protocol.md) for measurements and thresholds.

### Four motion tracks

| Track | Initial translation | Initial rotation | Condition |
| --- | --- | --- | --- |
| `static` | 0 m/s | 0 rad/s | Initially stationary |
| `drift` | 0.02 m/s | 0 rad/s | Translation without initial spin |
| `tumble` | 0.02 m/s | 0.5 rad/s | Translation and spin |
| `fast_tumble` | 0.05 m/s | 1.0 rad/s | Faster translation and spin |

The seed and object ID select the sign of the world-X linear velocity and world-Z angular velocity. Velocity is applied once at reset. A core plan contains **80 object–track episodes per seed**. Object pose, robot pose and camera configuration belong to the environment setup.

### The 20 core object instructions

Each row applies to all four tracks. The prompt names below retain the established object wording, including `l bracket` and `t fitting`.

| Object ID | Object name | English prompt |
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

### Objaverse expansion

Select `objaverse8414` to use the **8,414-object inventory**. The same capture template is filled with each record's source name after whitespace normalization. Source names are preserved, so a name may be a product title or contain non-English text. Object identity is carried by `object_id` and the asset catalog; similar names do not merge different objects.

The capture-only export contains **33,656 object–track instructions**. It provides the full list without embedding thousands of rows in this document. Names, category labels, attribution and selection rules are described in the [object guide](objects.md).

For a custom capture catalog, an optional `object_name` supplies the instruction name; otherwise the object ID is used with underscores replaced by spaces. Core and Objaverse names come from the registered inventories.

## Workcell instruction templates

Replace `{target_name}` with the exact target name in the tables below. These canonical instructions describe the measured goal; the [workcell protocol](workcells.md) defines the state thresholds, initial geometry and terminal hold.

| Task ID | English prompt template |
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

## MELFI V6: all 15 task–target instructions

The target IDs refer to the three boxes along the tray, rather than screen-relative left / right positions:

| Target ID | Prompt target name |
| --- | --- |
| `Front_quarter_box` | front quarter box |
| `Middle_quarter_box` | middle quarter box |
| `Rear_half_box` | rear half box |

Card transfer ends with the card held at the box opening. Insertion ends with the card released and retained inside. Extraction ends with the card held clear of the opening. Lid opening and closing are separate tasks with their own starting states.

| Task ID | Target ID | English prompt |
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

## RRM TB1: all 14 task–target instructions

The panel uses a wall mount with the arm directly in front on a floor plate; the [workcell guide](workcells.md#rrm-tb1) shows the installation. FDV1 uses the Multifunction Tool and Tertiary Cap Adapter; SMA uses the Safety Cap Tool and SMA Adapter; captive screws use the Safety Cap Tool and #10 Torque Set Adapter.

`SMA_r_c` identifies a physical array position: row increases along panel-local +Y and column along +X. Panel-local +Y maps to world +Z in the r003 wall layout: row 1 is at the bottom and row 3 at the top; columns 1 to 3 run left to right when facing the panel. Target IDs stay fixed when the camera moves. `captive_1` and `captive_2` address separate fastener positions. The default movable SMA target is `SMA_2_2`; the default captive target is `captive_1`. The guide explains how to rebuild other target variants and score them under the same plan.

| Task ID | Target ID | English prompt |
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

Cap removal includes retaining the cap in the adapter, docking that assembly in its holder and withdrawing the driver. A captive screw stays attached to the panel during both loosening and tightening.

## Select and record a task

```bash
astrobench plan assets.json --seed 42 --output capture-plan.json
astrobench workcell-plan --workcell all --repeats 10 --seed 42 \
  --asset-root assets/workcells --output workcell-plan.json

# Select one task and one concrete target
astrobench workcell-plan --workcell rrm_tb1 --task sma_remove_stow --target SMA_1_3 \
  --repeats 10 --seed 42 --output sma-1-3-plan.json
```

A workcell plan expands the task and target selection; ten repeats of all 29 combinations produce 290 episodes. Pass `episode["spec"]["language_prompt"]["text"]` to the policy together with the selected scene and target. The binding records the language-registry version and SHA-256, target identity and instruction-text SHA-256; the episode `spec_hash` covers all of them. Preserve the plan, trace and result identity when aggregating runs. Full setup and scoring commands are in the [workcell guide](workcells.md).
