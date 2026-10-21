# AstroBench workcell assets

This package contains the editable MELFI V6 mixed tray and RRM Task Board 1,
with named task parts, tool geometry, mounting hardware and SI-unit metadata.
The `.blend` files retain procedural surface finishes. The `.glb` files embed
geometry and portable metallic/roughness materials and have no external files.

## Load and reset

Open either `.blend` directly, or apply a task initial pose in Blender:

```bash
blender -b -P assets/workcells/load_asset.py -- \
  --asset melfi_v6 --task card_extract --target Rear_half_box \
  --save /tmp/melfi_extract.blend --receipt /tmp/melfi_reset.json
```

`load_asset.load()` and `load_asset.reset()` are also callable from a Blender
adapter. Reset positions the named geometry; the environment adapter measures
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
latches are individually named. `robot_attachment_frames` gives the original
fixed-base flange and scene placement; attach a runtime-supplied robot there.

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
