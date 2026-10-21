# Space manipulation workcells

[English](workcells.md) · [简体中文](workcells.zh-CN.md) · [Back to README](../README.md)

AstroBench includes two workcells with editable hardware, named moving parts and explicit completion goals. MELFI V6 covers sample storage in an ISS-style cabin. RRM TB1 covers cap and captive-screw servicing on a wall-mounted panel. Both use a fixed robot base and zero gravity; fixtures secure the equipment independently of gravity.

| MELFI V6 | RRM TB1 |
| :---: | :---: |
| <img src="media/melfi.png" alt="MELFI sample-storage workcell" width="420"> | <img src="media/rrm.png" alt="RRM servicing panel and tools" width="420"> |
| [GLB](../assets/workcells/melfi_v6/melfi_v6.glb) · [Blender](../assets/workcells/melfi_v6/melfi_v6.blend) · [Parts](../assets/workcells/melfi_v6/parts.json) | [GLB](../assets/workcells/rrm_tb1/rrm_tb1.glb) · [Blender](../assets/workcells/rrm_tb1/rrm_tb1.blend) · [Parts](../assets/workcells/rrm_tb1/parts.json) |

## Start with a reproducible plan

Run these commands from a cloned repository after installing the package. Models are stored in the repository; the Python package supplies the task catalog, planning and scoring tools.

```bash
astrobench workcells --output workcells.json
astrobench workcell-check-assets assets/workcells --output asset-check.json
astrobench workcell-plan --workcell all --repeats 10 --seed 42 \
  --asset-root assets/workcells --output workcell-plan.json
```

There are **9 task definitions and 29 task–target combinations**: 15 MELFI combinations and 14 RRM combinations. Ten repeats produce 290 episodes. `--workcell melfi_v6` selects MELFI only; `--workcell rrm_tb1` selects RRM only. Use `--task` to select particular tasks. With exactly one task, `--target` selects a particular box, cap or screw:

```bash
astrobench workcell-plan --workcell rrm_tb1 --task sma_remove_stow --target SMA_2_2 \
  --repeats 10 --seed 42 --asset-root assets/workcells --output sma-plan.json
```

This example plans ten episodes for the default movable SMA cap, `SMA_2_2`. Repeat `--target` to select additional targets for the same task; omit it to include every target of that task. For other RRM target positions, build the selected variant and pass its asset directory when scoring, as described below.

The `astrobench.workcell-plan/v2` plan binds the selected task, target, initial state, thresholds, asset identity and language instruction to the episode `spec_hash`. Pass `episode["spec"]["language_prompt"]["text"]` to the policy; its binding also records the registry version, registry hash and text hash. The same inputs reproduce the same plan. Execute each repeat independently using its recorded initial state and keep the plan beside the traces. Output files are created exclusively, so an existing file is not silently replaced.

## Tasks and targets

The [task and prompt catalog](tasks.md) lists the English instruction for every task and target. Use the instruction and `target_id` recorded in the episode plan.

All terminal conditions must hold over the final **1 second** of a **30-second** episode. Positions are in meters, angles in radians, times in seconds and forces in newtons. The table gives readable values; the machine-readable definitions are in [workcells.json](../astrobench/data/workcells.json).

| Task ID | Targets per repeat | Initial condition | Completion condition |
| --- | --- | --- | --- |
| `card_transfer_to_mouth` | 3 boxes | Card outside the box, gripper open | Grasp the card and hold it at the selected opening, within 5 mm and 5° of the goal. |
| `card_insert` | 3 boxes | Card held outside the selected box | Place the whole card inside the usable volume, within 5 mm and 5° of the insertion goal; release the gripper and establish retention force of at least 0.01 N. |
| `card_extract` | 3 boxes | Card retained inside the selected box | Grasp the card, clear the opening by at least 20 mm and hold it within 5 mm / 5° of the extraction goal. |
| `lid_open` | 3 boxes | Lid closed and latched | Release the latch and open the selected lid to at least 75°. |
| `lid_close` | 3 boxes | Lid open at 85° | Close to within 3°, close and engage the latch, and clear the tool by at least 50 mm. |
| `fdv1_remove_stow` | FDV1 | Cap seated and threaded | Unscrew, withdraw at least 60 mm, retain the cap in the adapter, dock it in the receiver and withdraw the driver. |
| `sma_remove_stow` | 9 SMA positions | Selected cap seated and threaded | Unscrew the requested cap, withdraw at least 35 mm, retain it in the adapter, dock it in the receiver and withdraw the driver. |
| `captive_loosen` | 2 screws | Screw tightened | Rotate at least 2.8 turns and reach 1.8–3 mm axial travel while remaining captive. |
| `captive_tighten` | 2 screws | Screw loosened by 3 turns / 2.1 mm | Return within 0.12 rad and 0.15 mm of the seated state, remain captive, disconnect and withdraw the tool. |

MELFI target IDs are `Front_quarter_box`, `Middle_quarter_box` and `Rear_half_box`. RRM target IDs are `FDV1`, `SMA_1_1` through `SMA_3_3`, and `captive_1` / `captive_2`. Select the target named in the episode; reaching a different cap or box does not satisfy the task.

The card tasks also check motion: linear speed at most 20 mm/s and angular speed at most 0.2 rad/s. Cap removal checks retention relative to the adapter before stowage: position within 3 mm, orientation within 3°, relative linear speed at most 10 mm/s, relative angular speed at most 0.1 rad/s and contact force at least 0.01 N. Final cap stowage requires an adapter pose within 2 mm of its receiver goal, both receiver latches closed, the flange captured, support contact, a detached driver more than 100 mm away and settled cap motion. A cap merely touched or lifted does not complete removal and stowage.

## Models and mounting

### MELFI V6

The storage tray follows the two-quarter-box and one-half-box arrangement shown in ESA's MELFI documentation. Quarter boxes have a 220 × 130 × 143 mm envelope; the half box is 220 × 270 × 143 mm. The modeled sample card measures 100 × 110 × 2 mm, with a 25 mm clear upper grasp region. Hinged, perforated lids, distinct lid and tray locks, insulation and sample restraints are separate parts.

The tray runs parallel to the wall. A floor-mounted column supports the robot in front of it, leaving access to the box openings. The asset retains these fixture and mounting coordinates so that a robot can be attached consistently across runs.

### RRM TB1

The panel includes an FDV1 tertiary cap, a 3 × 3 SMA cap array and two captive-screw positions. In the r003 layout, the panel is vertical on the cabin wall and the arm sits directly in front of it on a thin floor mounting plate. The arm unfolds toward the center of the panel; the cap receivers sit below the interface area. Use the supplied task and tool frames to align each tool with the panel normal.

| Front view | Side view |
| :---: | :---: |
| <img src="media/rrm-front.png" alt="Unfolded robot centered in front of the RRM panel" width="420"> | <img src="media/rrm-side.png" alt="Side view of the wall panel and floor-mounted robot" width="420"> |

The panel-frame origin is **983.45 mm above the cabin floor**. The robot base is **690 mm in front of the panel**, with its mounting surface **28 mm above the floor**. At the ready pose, the tool tip is **120 mm in front of the panel center**. Use the manifest mounting transforms to reproduce these installation dimensions.

| Interface | Tool pairing | Operation |
| --- | --- | --- |
| FDV1 tertiary cap | Multifunction Tool + Tertiary Cap Adapter | Capture the cap, unscrew it, withdraw axially and stow the adapter with the cap. |
| SMA cap | Safety Cap Tool + SMA Adapter | Address the selected cap, unscrew and withdraw it, then stow the adapter with the cap. |
| Captive screw | Safety Cap Tool + #10 Torque Set Adapter | Engage the recess and rotate; the screw stays attached throughout loosening and tightening. |

The task assets contain the workpieces, tools and supports. Attach your own robot and cabin assets using `robot_attachment_frames` in each manifest. Model coordinates and node mappings are recorded in `parts.json`; use those transforms instead of inferring scale or axes from a screenshot. GLB export follows the glTF coordinate convention; Blender and task metadata retain the documented asset frame.

Both assets provide collision descriptions and mesh archives: [MELFI collision geometry](../assets/workcells/melfi_v6/collision.json) and [RRM collision geometry](../assets/workcells/rrm_tb1/collision.json). Preserve holes, guide sleeves, tool recesses and retention geometry when creating collision shapes: replacing them with a single convex hull changes the task. See the [asset directory](../assets/workcells/) for file hashes, part mappings, references and rebuild sources. The authored models and sources use [Apache-2.0](../assets/workcells/LICENSE), with attribution in [NOTICE](../assets/workcells/NOTICE).

Use the [Blender loader](../assets/workcells/load_asset.py) to open the r003 centered ready layout, then save a selected task's starting geometry:

```bash
blender -b -P assets/workcells/load_asset.py -- --asset rrm_tb1 \
  --ready --placement world --save outputs/rrm-ready.blend
```

```bash
blender -b -P assets/workcells/load_asset.py -- --asset melfi_v6 \
  --task card_extract --target Rear_half_box --save outputs/melfi-extract.blend
blender -b -P assets/workcells/load_asset.py -- --asset rrm_tb1 \
  --task sma_remove_stow --target SMA_2_2 --placement world --save outputs/rrm-sma.blend
```

This resets the moving parts and tool placement. Each reset first restores the asset frame; applying `--placement world` afterward installs the reset RRM scene in the wall-and-floor layout. MELFI uses the released strap shape for transfer / insertion and the retained-around-card shape for extraction. The environment adapter implements `runtime_elastic_strip` using the supplied endpoint constraints and elastic parameters, then measures retention force from actual contacts. The reset itself supplies geometry; the adapter establishes the dynamics and records the measurements used below.

### Select another RRM cap or screw

The default RRM build has movable targets `FDV1`, `SMA_2_2` and `captive_1`. The source builder supports all nine SMA positions and both captive screws. For example, build SMA row 1 / column 3 and captive screw 2 in a separate directory, then load the selected target:

```bash
blender -b -P assets/workcells/publicbuild.py -- --asset rrm_tb1 \
  --sma-row 1 --sma-col 3 --captive-index 2 --output-root outputs/rrm-variant
blender -b -P assets/workcells/load_asset.py -- --asset-root outputs/rrm-variant \
  --asset rrm_tb1 --task sma_remove_stow --target SMA_1_3 --placement world \
  --save outputs/rrm-sma-1-3.blend
astrobench workcell-score workcell-plan.json EPISODE_ID trace.json \
  --asset-root outputs/rrm-variant --output sma-1-3-result.json
```

Use the `SMA_1_3` episode ID from the original full plan and the trace measured on this build. The output directory contains both workcells, source hashes and a manifest recording the build parameters and its original manifest identity. Scoring checks that the source files match the registered version and that the selected target is active, then records the actual asset identity with the result. The episode keeps its original plan identity, so all 29 target combinations can be aggregated in one report. See the [asset guide](../assets/workcells/README.md) for reset, collision unpacking and rebuilding details.

## Connect measured state to the scorer

The evaluator consumes state recorded by an environment adapter. Import the selected geometry, attach the robot, establish the task joints and restraints, reset to the episode's `initial_state`, then record synchronized measurements throughout the episode. Joint commands, planned poses and a generic grasp-success flag do not replace measured object state.

Every sample includes `t_s`, `measurement_time_s`, `target_id`, `linear_velocity_m_s`, `angular_velocity_rad_s`, `forbidden_contact` and `escaped`. The two timestamps must agree. Samples start at **0 seconds**, end at **30 seconds**, and have no gap greater than **25 ms**. Check the first measured state against the plan's initial geometry and measurement tolerances. Quaternions use **w, x, y, z** order and unit norm. Record vectors and scalars in SI units. Each sample must contain exactly the fields for the selected task.

| Task group | Additional measured fields |
| --- | --- |
| Card transfer / insert / extract | `goal_relative_position_m`, `goal_relative_quat_wxyz`, `gripper_aperture_m`, `gripper_target_contact_force_n`, `object_released`, `retention_force_n`, `min_containment_margin_m`, `opening_clearance_m` |
| Lid open / close | `lid_angle_rad`, `lid_latch_closed`, `lid_latch_engaged`, `driver_clearance_m` |
| FDV1 / SMA | `fastener_angle_rad`, `fastener_axial_m`, `thread_engaged`, `cap_adapter_position_m`, `cap_adapter_quat_wxyz`, `cap_adapter_linear_velocity_m_s`, `cap_adapter_angular_velocity_rad_s`, `cap_retention_force_n`, `adapter_goal_position_m`, `adapter_goal_quat_wxyz`, `receiver_support_force_n`, `receiver_latch_positions_m`, `receiver_flange_captured`, `driver_attached`, `driver_clearance_m` |
| Captive screw loosen / tighten | `fastener_angle_rad`, `fastener_axial_m`, `object_released`, `driver_attached`, `driver_clearance_m` |

Containment and opening clearance are signed distances for the **whole card mesh**, not its center. Fastener angle is accumulated rotation, not an angle reduced modulo 2π. Latch and release fields describe measured joint / geometry states. `receiver_latch_positions_m` contains the two measured latch offsets from their closed positions. Common velocities are measured in the fixed asset / world frame. `cap_adapter_position_m` and `cap_adapter_quat_wxyz` are residuals from the nominal retained cap-to-adapter transform, rather than the distance between their raw object origins. The Python API provides the exact field names and shapes:

```python
from astrobench.workcells import workcell_trace_fields

fields = workcell_trace_fields("fdv1_remove_stow")
```

For the cap residual, use the semantic binding's `adapter_object` and `nominal_retained_cap_in_adapter`: `inverse(nominal) @ inverse(world_from_adapter) @ world_from_cap`. The adapter is the detachable spindle; `driver_object` identifies the housing that withdraws after docking. Continue measuring the cap against the adapter after the driver disconnects.

For `adapter_goal_*`, the receiver frame is `tasks.fdv1.stowage.tool_pose_panel` or `tasks.sma.stowage.tool_pose_panel` in RRM's `collision.json`. These frames have identity rotation and translations `[0.06, -0.36, 0.016]` and `[0.23, -0.36, 0.016]` meters in the panel frame. The semantic `goal_frame_asset.target` instead identifies the cap's initial seat.

For cap tasks, `driver_attached` measures the driver-to-spindle coupling: it starts connected, with `driver_clearance_m: 0`, and disconnects after docking. For captive screws, the same field describes tool-to-screw engagement: it starts disengaged, with 100 mm clearance. Measure each according to its task interface.

The outer trace identifies the frozen episode:

```json
{
  "episode_id": "COPY_FROM_PLAN",
  "spec_hash": "COPY_FROM_PLAN",
  "samples": []
}
```

Replace the empty list with the adapter's complete measurements. Use the field specification above to construct each sample; this wrapper alone is not a runnable episode.

```bash
astrobench workcell-score workcell-plan.json EPISODE_ID trace.json \
  --asset-root assets/workcells --output episode-result.json
astrobench workcell-report workcell-plan.json results.json \
  --output workcell-report.json
```

Use the actual build directory for `--asset-root`; for a rebuilt RRM target, substitute the variant directory shown above. The Python equivalents are `resolve_workcell_episode(episode, asset_root=...)` and `score_workcell_trace(episode, samples, asset_root=...)` in `astrobench.workcells`. Resolution checks the active target and its registered source; scoring preserves the canonical episode identity and records `evaluated_asset_manifest_sha256`, `evaluated_binding` and `evaluated_asset_provenance`.

`results.json` is an array of episode result objects. Results include stage progress, failure reasons, terminal hold duration and a trace checksum. A measured task failure is a completed evaluation with `strict_success: false`; a malformed trace has `status: invalid` and `strict_success: null`. The report groups outcomes by task and target, retains runtime errors and unrun episodes, and distinguishes success among completed episodes from the fraction of the whole plan completed successfully. `full_plan_success_rate` becomes available when all planned episodes have valid completed outcomes. Keep the plan, traces, result objects and report together.

## Reference fidelity and recorded checks

NASA / ESA publications establish the visible hardware, dimensions and task sequence. AstroBench reconstructs the visible parts and supplies robot placement, internal tool mechanisms and scoring tolerances as engineering choices. The two-quarter / one-half MELFI configuration is documented in ESA's 2002 article; NASA's 2015 interface document notes the later phase-out of quarter boxes. MELFI V6 has a 26-pose card-transfer geometry check ending at the box opening. The three linked videos record RRM scripted functional trials in the original tabletop layout, covering FDV1 removal/stowage, the central SMA cap removal/stowage and one captive-screw loosen–tighten cycle; their local tool/contact checks and arm geometry checks are separate from the 29-combination task catalog and the new scoring protocol.

The r003 wall layout has a separate 335-pose CAD / inverse-kinematics review: one centered ready pose, 226 transformed mechanism-trajectory poses, and 108 approach / withdrawal poses across all 12 operation targets. No non-task floor, wall, self or tool–arm collision was found in the sampled poses. These are layout checks; the three videos retain their original mechanism-trial provenance.

[▶ FDV1 trial](media/fdv1.mp4) · [▶ SMA trial](media/sma.mp4) · [▶ Captive-screw trial](media/captive.mp4)

## Primary references

| Source | What it supports |
| --- | --- |
| [ESA Bulletin 109 — MELFI (2002)](https://www.esa.int/esapub/bulletin/bullet109/chapter5_bul109.pdf) | Printed pp. 40–41 / PDF pp. 6–7: the two-quarter / one-half arrangement, sample cards and elastic restraints. |
| [NASA SSP 57000 Rev. R (2015)](https://ntrs.nasa.gov/api/citations/20190001390/downloads/20190001390.pdf#page=327) | Appendix H, H-30–H-32: box handling, locks, dimensions and drawings. |
| [NASA — Rick Mastracchio Replaces Science Freezer Tray](https://www.nasa.gov/image-article/rick-mastracchio-replaces-science-freezer-tray/) | In-orbit MELFI tray handling photograph. |
| [NASA — RRM thermal design paper (2011)](https://ntrs.nasa.gov/api/citations/20110013452/downloads/20110013452.pdf#page=3) | Task-board configuration, cap and fastener groups, and tool views. |
| [NASA — RRM Phase 1](https://www.nasa.gov/nexis/rrm-phase-1/) | Tool roles and the RRM servicing sequence. |
| [NASA — Refueling Demonstration Proves Viability (8 February 2013)](https://www.nasa.gov/news-release/nasas-refueling-demonstration-proves-viability-of-satellite-servicing-technologies/) | Completed robotic cap removal and stowage in the RRM campaign. |
| [NASA ISS Daily Summary (3 May 2013)](https://www.nasa.gov/blogs/stationreport/2013/05/03/iss-daily-summary-report-05-03-13/) | Planned SMA cap operations using the SMA Adapter and stowage receptacle. |
| [NASA ISS Daily Summary (7 May 2013)](https://www.nasa.gov/blogs/stationreport/2013/05/07/iss-daily-summary-report-05-07-13/) | Completed fastener retightening using the #10 Torque Set Adapter. |

