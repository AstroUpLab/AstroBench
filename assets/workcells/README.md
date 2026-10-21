# AstroBench workcell assets

This package contains the editable MELFI V6 mixed tray and RRM Task Board 1,
with named task parts, tool geometry, mounting hardware and SI-unit metadata.
RRM uses a vertical wall mount and a floor plate centered in front of the panel.
The `.blend` files retain procedural surface finishes. The `.glb` files embed
geometry and portable metallic/roughness materials and have no external files.

## Load and reset

Open either `.blend` directly, or apply a task initial pose in Blender:

```bash
blender -b -P assets/workcells/load_asset.py -- \
  --asset melfi_v6 --task card_extract --target Rear_half_box \
  --save /tmp/melfi_extract.blend --receipt /tmp/melfi_reset.json
```

`load_asset.load()`, `load_asset.reset()` and `load_asset.place()` are also
callable from a Blender adapter. Apply `place(parts, 'world', report)` after
resetting to use the configured wall/floor layout; repeated placement is
idempotent, and reset restores the intrinsic asset frame. Reset positions the named geometry; the environment adapter measures
contacts, retention, velocities and task completion after resetting its robot
and physics state. No trajectory or motion policy is embedded.

MELFI accepts `card_transfer_to_mouth`, `card_insert`, `card_extract`,
`lid_open`, and `lid_close`, on each of `Front_quarter_box`,
`Middle_quarter_box`, and `Rear_half_box`. Each box has a separate lid joint.

RRM accepts `fdv1_remove_stow`, `sma_remove_stow`, `captive_loosen`, and
`captive_tighten`. The default movable targets are `FDV1`, `SMA_2_2` and
`captive_1`. Rebuild to select any of the nine SMA positions or either captive
fastener:

```bash
blender -b -P assets/workcells/publicbuild.py -- \
  --asset rrm_tb1 --sma-row 1 --sma-col 3 --captive-index 2 \
  --output-root /tmp/astrobench_assets
blender -b -P assets/workcells/load_asset.py -- \
  --asset-root /tmp/astrobench_assets --asset rrm_tb1 \
  --task captive_tighten --target captive_2 --save /tmp/captive_2.blend
```

Rebuilding creates a new asset manifest with the chosen target, source-file
hashes and `derived_from_manifest_sha256`. Keep the original manifest and
record the derived manifest identity with the run. The output root includes
both workcells and the self-contained source package.

## RRM wall mount and centered ready pose

```bash
blender -b -P assets/workcells/load_asset.py -- \
  --asset rrm_tb1 --ready --placement world \
  --save /tmp/rrm_ready.blend --receipt /tmp/rrm_ready.json
blender -b -P assets/workcells/load_asset.py -- \
  --asset rrm_tb1 --task fdv1_remove_stow --target FDV1 --placement world \
  --save /tmp/rrm_fdv1.blend
```

The panel centre is `(0, -0.16, 1.10)` m in world coordinates. The arm mounting
frame is `(0, -0.85, 0.14455)` m with +90° yaw: the arm stands directly in front
of the panel on a 28 mm floor plate. Four stand-offs connect the panel to its
wall backplate; the two tool docks have their own wall spacers. The support
geometry includes floor anchors and the supply cable routed along the floor
and wall. The wall is at Y = −0.029108 m and the floor at Z = 0.11655 m.

`rrm_tb1/source/layout_config.json` contains the complete world transform,
mounting frame and centered waiting configuration. The tool tip sits 120 mm
in front of the panel centre. `ready_pose` records seven Panda joint angles,
Robotiq 2F-85 joint values, and TCP/tool transforms for a runtime-supplied
robot. It is a static waiting configuration, separate from task initial poses.
The source builder reconstructs the support hardware without cabin or robot
mesh dependencies. Task parts and contact frames remain in the panel-local
asset frame so target variants share the same task geometry.

The loader makes the selected tool visible and deactivates the other tool
variants; the reset receipt lists their object names. Runtime collision
adapters should apply the same selection to `tool/<kind>` body families.
The collision archive includes named wall/floor proxies; these two proxy
meshes are not part of the visible model. They match the layout datums and
can be replaced by corresponding cabin collision surfaces.

## Coordinate and joint conventions

`parts.json` uses metres, radians and Z-up asset coordinates. Its matrices are
row-listed 4×4 matrices acting on column vectors. Each named node records
both its asset and parent transform. `semantic_targets` maps task identifiers
to exact Blender/GLB object names, task frames and the movable target.
`manifest.json` lists file SHA256 hashes and the GLB coordinate conversion.

MELFI's tray extends along +Y. The card is 100 × 110 mm and is oriented at
−90° about asset Z for insertion. The lid hinge rotates about its local +Y;
closed is 0° and open is 85°. The separate latch paddle uses its own pose.
Opening, inserted and approach frames are engineering task frames expressed
at the card centre. The inserted pose leaves the card bottom 0.5 mm above the
inner floor. Each box provides released and retained-around-card band poses;
transfer/insertion starts released, and extraction starts with the band around
the card. The semantic binding includes endpoint constraints and elastic-strip
parameters. Resolve those constraints and contacts in the runtime, then measure
retention force after settling; a visible pose alone supplies no force.

RRM's panel lies in XY with +Z pointing away from its front surface. Cap and
captive-screw axes are +Z. `joints` records the screw pitches, travel limits
and tool spindle axes. The FDV1/SMA adapters, jaws, retaining leaves and dock
latches are individually named. `robot_attachment_frames` gives the floor mounting flange and
`world_from_asset` transform; attach a runtime-supplied robot there.
`load_asset.ready()` supplies the centered static configuration, while task
reset selects the appropriate tool and initial fastener state.

## Collision geometry

```bash
python assets/workcells/unpack_collision.py assets/workcells/rrm_tb1
python assets/workcells/unpack_collision.py assets/workcells/melfi_v6
```

The unpacker verifies the archive hash, rejects path traversal and symlinks,
and preserves different existing meshes. OBJ references in `collision.json`
are relative to that JSON file. RRM moving bodies use convex material pieces
that preserve the hollow cap and tool cavities. Fixed hardware uses concave
triangle surfaces. MELFI uses static concave hardware surfaces, a compound
sample-card collider, named kinematic lid surfaces, and runtime elastic strips.
The bands and their free-end hardware are excluded from static collision; a backend using fully
dynamic lids should decompose the lid material while preserving its openings.

## Rebuild

```bash
blender -b -P assets/workcells/publicbuild.py -- --asset all
```

Built with Blender 5.2. All geometry sources are in the adjacent `source/`
directories. Units and task bindings are generated with the geometry.
Apache-2.0 covers the new code and original geometry in this directory. See
[LICENSE](LICENSE) and [NOTICE](NOTICE) for licensing and original hardware
references.
