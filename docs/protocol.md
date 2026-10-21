# Capture and retention protocol

AstroBench provides deterministic episode plans, resolved language instructions,
scoring of synchronized state measurements, and result aggregation for
**free-floating objects manipulated by a fixed-base arm in zero gravity**.
The environment adapter loads the object and robot geometry, applies each
initial state, runs the policy, and records the measurements used by the scorer.

## Install and run

Python 3.11+; the package has no runtime dependencies and needs no GPU.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
astrobench plan examples/catalog.json --object-set custom --seed 42 --output plan.json
python -c 'import json; print(json.load(open("plan.json"))["episodes"][0]["episode_id"])'
```

The synthetic example demonstrates the catalog format. For an evaluation,
provide each object's `object_id`, actual `asset_sha256`, `geometry_group` and
`split` (`train`, `validation`, or `test`). Keep related geometry variants in the
same split and review the group assignments when assembling the catalog. The
planner checks that identical assets and geometry groups do not cross splits.
An optional `object_name` names a custom object in its language instruction.

The plan includes every selected object under four tracks: `static`, `drift`,
`tumble` and `fast_tumble`. The seed and object ID determine the signs of the
world-X linear velocity and world-Z angular velocity. The [task catalog](tasks.md)
lists their speed values and instructions. The emitted condition is `S`, the
zero-gravity cabin setting. Each plan records the selected assets, initial motion
and episode identities for reproducible scoring.

## Language instruction and plan identity

The current planner writes `astrobench.plan/v2`. Every episode contains the resolved policy instruction at `episode["spec"]["language_prompt"]["text"]`, with the prompt-registry version and SHA-256, selected object identity and instruction-text SHA-256. The episode `spec_hash` binds this language record together with the asset and motion specification. The capture judge and measurement thresholds are unchanged.

The capture instruction is `Capture the {object_name} and hold it securely.` across all four tracks. The [complete task catalog](tasks.md) lists core object names, all workcell instructions and the Objaverse export command. Export the language records independently with:

```bash
astrobench task-prompts --scope capture --output capture-prompts.json
```

After an adapter produces a trace for a registered episode:

```bash
astrobench score plan.json EPISODE_ID trace.json --output episode-result.json
astrobench report plan.json results.json --output report.json
```

`results.json` is a JSON array of episode results. Outputs use exclusive creation
to avoid overwriting evidence. Runtime errors require the seven identity fields,
`status: "runtime_error"`, and `strict_success: null`; timeouts are completed
failures, not runtime errors. Missing episodes stay visible and incomplete suites
have no full macro score. Run each policy/checkpoint separately; do not pool them.

## Trace and adapter contract

Trace envelope: `{"episode_id": "...", "spec_hash": "...", "samples": [...]}`.
Each sample has exactly these fields (SI units):

| Field | Measurement |
|---|---|
| `t_s` | Simulation time, starting at zero and ending at 12 s |
| `left_target_force_n`, `right_target_force_n` | Contact force magnitude for each finger against the selected target only |
| `closed` | Measured gripper closure, not the close command |
| `forbidden_contact` | Support or other disallowed contact under the task's contact whitelist |
| `escaped` | Target outside the task's fixed workspace boundary |
| `relative_linear_speed_m_s` | Norm of target velocity in the gripper frame, including the rotating-frame term |
| `relative_angular_speed_rad_s` | Norm of target/gripper relative angular velocity |
| `relative_position_m` | Target COM position in gripper coordinates, three numbers |
| `relative_quat_wxyz` | Unit target orientation quaternion relative to the gripper |

Maximum sample gap: 25 ms. At nominal 50 Hz use 601 samples including t=0 and
t=12. Sensors must be sampled synchronously. Inputs must be finite, with explicit
booleans. Truncated traces are rejected, never silently counted as task failures.

Capture is diagnosed after one second of bilateral contact, actual closure,
bounded relative motion and pose excursion. Primary success requires such a
continuous window **ending at the episode horizon**. A transient early grasp
followed by loss is a failure. Pose excursions are measured against the start of
the current candidate segment. Scoring operates on the recorded samples.
MELFI and RRM manipulation goals use the separate [workcell judges](workcells.md).

The adapter must verify asset bytes, freeze robot and scene configuration, read
back gravity and initial conditions, remove support collision, and set initial
linear and angular velocities once at reset. Subsequent target motion follows
the environment dynamics.
Record simulator version, solver settings, timestep, robot/gripper version,
controller and camera calibration, action units/frame/rate, checkpoint SHA256,
hardware and seeds beside each trace. The adapter supplies these environment
measurements; the scorer checks the trace against the registered episode and
applies the capture-and-retention criteria.

