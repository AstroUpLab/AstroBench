# Object collections and cabin scenes

## Select a collection

| Collection | Count | CLI option |
| --- | ---: | --- |
| Core | 20 classes | `core20` (default) |
| Objaverse expansion | 8,414 object instances | `objaverse8414` |

```bash
astrobench objects --output core20.json
astrobench objects --object-set objaverse8414 --output objaverse8414.json
```

Each export contains the collection ID, object count, inventory SHA-256 and object records. The core preserves its original object ordering. Objaverse records include the source UID, object name, LVIS labels, group, source URL, author, license and selection reason. The expansion represents 51 LVIS labels plus objects without LVIS annotations. Instance and class counts are recorded separately.

The inventory is packaged with the Python distribution. SHA-256 is checked against the decompressed inventory bytes before export. Use a fresh output filename for each invocation.

## Generate episode plans

The planner reads an asset catalog containing `object_id`, `asset_sha256`, `geometry_group` and `split`. Match `object_id` to the exported inventory; Objaverse IDs use `objaverse_<source_uid>`.

```bash
astrobench plan assets.json --seed 42 --output core20-plan.json
astrobench plan assets.json --object-set objaverse8414 --seed 42 --output expanded-plan.json
astrobench plan examples/catalog.json --object-set custom --seed 42 --output example-plan.json
```

`core20` selects the twenty core IDs. `objaverse8414` selects all expansion IDs. `custom` uses the supplied catalog. Selection checks duplicate and missing IDs; the protocol validates asset hashes, geometry groups and splits. The plan records the selected assets and motion conditions in episode identity hashes. See [the protocol reference](protocol.md) for trajectories, scoring and reporting.

## Category and name screening

The collection originates from the 798,759 indexed objects in Objaverse 1.0, pinned to revision `556637099bf4fa79ea7b239d0d9c328b8a2e9ac8`. The screening rules are stored in `astrobench/data/objaverse_rules.json`; source and selection hashes are in `astrobench/data/objaverse_source.json`.

The rules select rigid hand tools, containers, portable electronics, mechanical parts, scientific equipment and cabin supplies. They normalize names and compare whole tokens, category labels and specific part phrases. Scenes, buildings, furniture, full vehicles, living organisms and unsuitable decorative objects are filtered out. Ambiguous names and conflicting labels are retained in a review list. The distributed selection uses CC0 or CC BY source metadata, with attribution retained per object.

Rebuild the selection from the pinned metadata:

```bash
python scripts/astrobench_fetch_objaverse_metadata.py --cache outputs/objaverse_metadata --workers 6
python scripts/astrobench_filter_objaverse.py \
  --metadata outputs/objaverse_metadata/metadata \
  --lvis outputs/objaverse_metadata/lvis-annotations.json.gz \
  --rules astrobench/data/objaverse_rules.json \
  --output outputs/objaverse_selection
```

Outputs include the complete decision log, selected records, UID list, category counts, input hashes and metadata coverage. Source objects retain their individual licenses and author attribution.

## Cabin scene configuration

```bash
astrobench scenes --output scenes.json
```

The default is `iss_jpm`. Additional configurations are `iss_us_lab`, `iss_eu_lab`, `iss_node2` and `iss_cupola`. The Cupola worksite places the workspace in the adjoining Node 3 interior. Cabin backgrounds use NASA Astrobee ISS assets; the robot base stays fixed and task body definitions and initial states are reused across cabins.

The task layout combines the 20 core objects with static and dynamic initial conditions, plus ten operation families: cabinet door, drawer, panel button, knob/valve, lever, peg insertion, plug, module seating, reorientation, and stow/close. Reversible operations use separate directions, giving fifteen operation subitems per cabin configuration.

Sources: [Objaverse documentation](https://objaverse.allenai.org/docs/objaverse-1.0/), [pinned metadata](https://huggingface.co/datasets/allenai/objaverse/tree/556637099bf4fa79ea7b239d0d9c328b8a2e9ac8), [NASA ISS assets](https://github.com/nasa/astrobee_media/tree/master/astrobee_iss).
