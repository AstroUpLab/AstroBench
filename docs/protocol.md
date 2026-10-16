# AstroBench — portable evaluation protocol (local research preview)

Evaluate **free-floating objects with a fixed-base arm** in an ideal zero-gravity
cabin. This distribution extracts the repository's strict aggregation code and
adds a versioned capture/retention judge and deterministic episode manifests.
It is **not yet a portable Isaac Sim environment or a measured leaderboard**.
The current thresholds and motion tracks are draft settings awaiting calibration.

## Install and run

Python 3.11+; the package has no runtime dependencies and needs no GPU.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
astrobench plan examples/catalog.json --seed 42 --output plan.json
python -c 'import json; print(json.load(open("plan.json"))["episodes"][0]["episode_id"])'
```

The example catalog is explicitly synthetic, has no associated physical asset,
and tests protocol plumbing only. Replace it with a catalog of verified assets.
Each object must have `object_id`, the actual `asset_sha256`, a `geometry_group`
that groups related asset variants, and `split` (`train`, `validation`, or `test`).
Asset bytes and geometry groups may not cross splits. Group assignments require
manual audit; hashes cannot detect semantically equivalent geometry by themselves.

The plan enumerates every object under static, drift, tumble and faster-tumble
tracks. Directions are seed-dependent. This is **not** procedural shape generation
or a claim of random SO(3) motion coverage. The fast track is a proposed dynamics
holdout: exclude it from training explicitly; the generator itself does not run
training or enforce training-data access. Only S (cabin / ideal 0g) is emitted.

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
the current candidate segment. This is a sampled-data criterion; contacts between
samples are not certified. Insertion and stow/release need separate task judges.

The adapter must verify asset bytes, freeze robot and scene configuration, read
back gravity and initial conditions, remove support collision, set initial linear
and angular velocities once at reset, and never servo the object trajectory.
Record simulator version, solver settings, timestep, robot/gripper version,
controller and camera calibration, action units/frame/rate, checkpoint SHA256,
hardware and seeds beside each trace. These physical checks are not performed by
the CPU judge. Hash binding detects accidental identity drift, not dishonest logs.

