"""Hash-bound plans and terminal retention scoring, independent of a simulator.

Trace fields are measurements supplied by an adapter, not policy predictions.
This evaluates a capture/retention task only; insertion/stow need other judges.
"""
import hashlib
import json
import math
from copy import deepcopy

PROTOCOL = {
    "version": "astrobench.capture-retain/0.1-draft",
    "gravity_m_s2": 0.0, "robot_base": "fixed",
    "hold_s": 1.0, "max_sample_gap_s": 0.025,
    "min_finger_force_n": 0.5, "max_relative_linear_speed_m_s": 0.02,
    "max_relative_angular_speed_rad_s": 0.2,
    "max_relative_translation_m": 0.01, "max_relative_rotation_rad": 0.1,
    "horizon_s": 12.0,
}
TRACKS = {
    "static": (0.0, 0.0), "drift": (0.02, 0.0), "tumble": (0.02, 0.5),
    "fast_tumble": (0.05, 1.0),
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def number(value, name, minimum=0):
    if type(value) not in (int, float) or not math.isfinite(value) or value < minimum:
        raise ValueError(f"{name}: finite number >= {minimum} required")
    return value


def vector(value, size, name):
    if not isinstance(value, list) or len(value) != size:
        raise ValueError(f"{name}: length-{size} list required")
    return [number(v, name, -float('inf')) for v in value]


def make_plan(catalog, seed=0):
    """Catalog groups must be disjoint; every registered object gets every track.

    Seed determines signed velocity direction, not geometry or camera pose.
    Asset SHA256 is a declared identity; validate its bytes on the target host.
    """
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise ValueError("seed must be uint64")
    if not isinstance(catalog, list) or not catalog:
        raise ValueError("nonempty catalog required")
    ids, hashes, groups = set(), {}, {}
    for obj in catalog:
        if set(obj) != {"object_id", "asset_sha256", "split", "geometry_group"}:
            raise ValueError("exact catalog fields required")
        if any(type(v) is not str or not v or v.strip() != v for v in obj.values()):
            raise ValueError("nonempty catalog labels required")
        ident, sha, split, group = (obj[k] for k in ('object_id','asset_sha256','split','geometry_group'))
        if ident in ids or split not in ('train', 'validation', 'test'):
            raise ValueError("duplicate object or invalid split")
        if len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            raise ValueError("asset SHA256 required")
        for table, key in ((hashes, sha), (groups, group)):
            if key in table and table[key] != split:
                raise ValueError("asset/geometry-group leakage across splits")
            table[key] = split
        ids.add(ident)
    episodes = []
    for obj in sorted(catalog, key=lambda o:o['object_id']):
        for track, (speed, spin) in TRACKS.items():
            bits = int(digest([seed, obj['object_id']]), 16)
            # Shared directions across difficulty tracks allow paired diagnosis.
            spec = {"object": deepcopy(obj), "track": track,
                    "linear_velocity_world_m_s": [speed * (-1 if bits & 1 else 1), 0, 0],
                    "angular_velocity_world_rad_s": [0, 0, spin * (-1 if bits & 2 else 1)],
                    "initial_motion_mode": "reset_once", "protocol": deepcopy(PROTOCOL)}
            token = digest([obj['object_id'], seed])[:16]
            episodes.append(dict(episode_id=f"{token}/{track}", task_id="capture_retain",
                suite=f"{obj['split']}/{track}", condition="S", pair_id=token,
                seed=seed, spec_hash=digest(spec), spec=spec, protocol=deepcopy(PROTOCOL)))
    catalog = sorted(deepcopy(catalog), key=lambda o:o['object_id'])
    return {"schema": "astrobench.plan/v1", "status": "draft_uncalibrated", "seed": seed,
            "catalog": catalog, "catalog_sha256": digest(catalog), "episodes": episodes}


def validate_plan(plan):
    if plan.get('schema') != 'astrobench.plan/v1' or not plan.get('episodes'):
        raise ValueError("nonempty astrobench plan required")
    seen = set()
    for ep in plan['episodes']:
        if ep['episode_id'] in seen:
            raise ValueError("duplicate episode")
        seen.add(ep['episode_id'])
        if ep['spec_hash'] != digest(ep['spec']):
            raise ValueError("episode spec hash mismatch")
        if ep['protocol'] != PROTOCOL or ep['spec']['protocol'] != PROTOCOL:
            raise ValueError("unsupported protocol; version and calibrate a new scorer")
    if digest(plan) != digest(make_plan(plan['catalog'], plan['seed'])):
        raise ValueError("plan differs from canonical catalog/seed/track expansion")
    return plan


def score_trace(samples, protocol=None):
    """Return terminal-window retention; an early transient grasp cannot pass.

    Samples cover t=0 through the fixed horizon, with gaps <= max_sample_gap_s.
    In each contact segment pose excursions are measured from its first pose.
    Unobserved inter-sample contacts are outside this sampled-data contract.
    """
    p = PROTOCOL if protocol is None else protocol
    if p != PROTOCOL:
        raise ValueError("unsupported protocol")
    if not isinstance(samples, list) or not samples:
        raise ValueError("nonempty trace required")
    start = anchor = None
    first_capture = None
    prev = None
    longest = 0.0
    losses = 0
    was_stable = False
    fields = {'t_s','left_target_force_n','right_target_force_n','closed',
              'forbidden_contact','escaped','relative_linear_speed_m_s',
              'relative_angular_speed_rad_s','relative_position_m','relative_quat_wxyz'}
    for sample in samples:
        if set(sample) != fields:
            raise ValueError("exact trace fields required")
        t = number(sample['t_s'], 't_s')
        if prev is None:
            if t != 0: raise ValueError("trace must start at zero")
        elif not 0 < t-prev <= p['max_sample_gap_s'] + 1e-9:
            raise ValueError("timestamps must increase without missing intervals")
        if t > p['horizon_s'] + 1e-9: raise ValueError("trace exceeds horizon")
        for key in ('closed','forbidden_contact','escaped'):
            if type(sample[key]) is not bool: raise ValueError(f"{key}: boolean required")
        for key in ('left_target_force_n','right_target_force_n',
                    'relative_linear_speed_m_s','relative_angular_speed_rad_s'):
            number(sample[key], key)
        pos = vector(sample['relative_position_m'],3,'position')
        quat = vector(sample['relative_quat_wxyz'],4,'quaternion')
        if abs(sum(v*v for v in quat)-1) > 1e-5: raise ValueError("unit quaternion required")
        good = (sample['closed'] and not sample['forbidden_contact'] and not sample['escaped']
            and min(sample['left_target_force_n'], sample['right_target_force_n']) >= p['min_finger_force_n']
            and sample['relative_linear_speed_m_s'] <= p['max_relative_linear_speed_m_s']
            and sample['relative_angular_speed_rad_s'] <= p['max_relative_angular_speed_rad_s'])
        if good and anchor is not None:
            distance = math.dist(pos, anchor[0])
            angle = 2*math.acos(min(1, abs(sum(a*b for a,b in zip(quat, anchor[1])))))
            if distance > p['max_relative_translation_m'] or angle > p['max_relative_rotation_rad']:
                good = False
        if good:
            if start is None: start, anchor = t, (pos, quat)
            duration = t-start
            longest = max(longest, duration)
            stable = duration + 1e-9 >= p['hold_s']
            if stable and first_capture is None: first_capture = t
        else:
            stable = False
            if was_stable: losses += 1
            start = anchor = None
        was_stable = stable
        prev = t
    if abs(prev-p['horizon_s']) > 1e-9:
        raise ValueError("incomplete trace: full horizon required")
    return dict(strict_success=was_stable, time_to_stable_capture_s=first_capture,
                longest_stable_candidate_s=longest, certified_grasp_losses=losses,
                terminal_hold_s=prev-start if start is not None else 0.0,
                judge=p['version'])
