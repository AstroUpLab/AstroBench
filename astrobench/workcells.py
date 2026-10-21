"""Portable, measured-state contracts for MELFI and RRM manipulation.

An environment adapter supplies synchronized measurements. Policy ``success``
flags, phases and commands are not input to the judge. No control policy,
collection loop, learned model or simulator dependency is included here.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from importlib.resources import files
import hashlib
import json
import math
from pathlib import Path

from .metrics import wilson95
from .prompts import workcell_prompt


class WorkcellValidationError(ValueError):
    """A plan, state stream or result is incompatible with this contract."""


def _finite_json(value, path="value"):
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for i, v in enumerate(value):
            _finite_json(v, f"{path}[{i}]")
        return
    if type(value) is dict:
        for k, v in value.items():
            if type(k) is not str:
                raise WorkcellValidationError(f"{path}: string JSON keys required")
            _finite_json(v, f"{path}.{k}")
        return
    raise WorkcellValidationError(f"{path}: finite JSON value required")


def _digest(value):
    _finite_json(value)
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _sha(value, name):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise WorkcellValidationError(f"{name}: lowercase SHA256 required")
    return value


def _number(value, name, low=-math.inf):
    if type(value) not in (int, float) or not math.isfinite(value) or value < low:
        raise WorkcellValidationError(f"{name}: finite number >= {low} required")
    return value


def _vector(value, size, name):
    if type(value) is not list or len(value) != size:
        raise WorkcellValidationError(f"{name}: length-{size} JSON array required")
    return [_number(v, name) for v in value]


def _quaternion(value, name):
    q = _vector(value, 4, name)
    if abs(sum(x*x for x in q)-1.) > 1e-6:
        raise WorkcellValidationError(f"{name}: unit wxyz quaternion required")
    return q


def _norm(v):
    return math.sqrt(sum(x*x for x in v))


def _angle(q):
    return 2*math.acos(min(1., abs(q[0])))


def _base_catalog():
    return json.loads(files('astrobench').joinpath('data/workcells.json').read_text())


def _variant_targets(canonical, workcell, args):
    expected = deepcopy(canonical['semantic_targets'])
    if workcell == 'melfi_v6':
        if args != {}: raise WorkcellValidationError('MELFI has no build selection arguments')
        return expected
    if type(args) is not dict or set(args) != {'sma_row','sma_col','captive_index'}:
        raise WorkcellValidationError('exact RRM target build arguments required')
    for key, upper in (('sma_row',3),('sma_col',3),('captive_index',2)):
        if type(args[key]) is not int or not 1 <= args[key] <= upper:
            raise WorkcellValidationError('invalid RRM target build argument')
    for target, binding in expected.items():
        chosen = dict(args)
        if target.startswith('SMA_'):
            _, row, col = target.split('_'); row, col = int(row), int(col)
            active = (row,col) == (args['sma_row'],args['sma_col'])
            chosen.update(sma_row=row,sma_col=col)
            seat = [(col-2)*.022,(row-2)*.022,.010]
        elif target.startswith('captive_'):
            index = int(target.rsplit('_',1)[1]); active = index == args['captive_index']
            chosen['captive_index'] = index
            name = 'RRM_TB1_TASK_captive_moving_screw' if active else f'RRM_TB1_Captive_fastener_{index}'
            binding['root_object'] = binding['moving_object'] = name
            seat = [0,0,0]
        else:
            active, seat = True, [0,0,.012]
        binding['active'] = active
        binding['rebuild'] = chosen
        if active: binding['seat_position_parent'] = seat
        else: binding.pop('seat_position_parent',None)
    return expected


def _validate_asset_binding(asset, canonical, workcell):
    if type(asset) is not dict or set(asset) != set(canonical):
        raise WorkcellValidationError('exact asset binding fields required')
    _sha(asset['manifest_sha256'], 'asset manifest SHA256')
    if asset['manifest_sha256'] == canonical['manifest_sha256']:
        if _digest(asset) != _digest(canonical):
            raise WorkcellValidationError('canonical asset metadata changed')
        return
    for key in ('manifest_path','units','up_axis','source_files','canonical_source_sha256',
                'layout','ready_pose','robot_attachment_frames'):
        if asset.get(key) != canonical.get(key):
            raise WorkcellValidationError(f'derived asset changes canonical source/placement: {key}')
    if asset['derived_from_manifest_sha256'] != canonical['manifest_sha256']:
        raise WorkcellValidationError('derived asset must identify canonical manifest')
    if _digest(asset['semantic_targets']) != _digest(_variant_targets(canonical,workcell,asset['build_args'])):
        raise WorkcellValidationError('derived target geometry/bindings differ from allowed selection')


def _catalog_with_bindings(bindings):
    catalog = _base_catalog()
    if type(bindings) is not dict or set(bindings) != set(catalog['assets']):
        raise WorkcellValidationError('exact asset inventory required')
    for workcell, asset in bindings.items():
        _validate_asset_binding(asset,catalog['assets'][workcell],workcell)
    catalog['assets'] = deepcopy(bindings)
    return catalog


def workcell_catalog(asset_root=None):
    """Return task contracts and pinned asset identities, without cwd lookup.

    ``asset_root`` explicitly selects a directory containing melfi_v6/ and
    rrm_tb1/. Its manifests and every declared file checksum are verified.
    Without it, the package's bundled, pinned metadata is returned; loading
    the asset bytes remains the environment adapter's responsibility.
    """
    catalog = _base_catalog()
    if asset_root is not None:
        from .workcell_assets import check_workcell_assets
        check_workcell_assets(asset_root)
        root = Path(asset_root).resolve()
        for workcell, asset in catalog['assets'].items():
            path = root / asset['manifest_path']
            if not path.is_file():
                raise WorkcellValidationError(f"missing asset manifest: {path}")
            raw = path.read_bytes()
            manifest = json.loads(raw)
            _finite_json(manifest, 'asset manifest')
            if manifest.get('asset_id') != workcell:
                raise WorkcellValidationError('asset manifest identity mismatch')
            if manifest.get('schema') != 'astrobench.workcell.asset.v1':
                raise WorkcellValidationError('unsupported asset manifest schema')
            actual = hashlib.sha256(raw).hexdigest()
            candidate = {'manifest_path':asset['manifest_path'],'manifest_sha256':actual,
                         'semantic_targets':manifest.get('semantic_targets'),
                         'units':manifest.get('units'),'up_axis':manifest.get('up_axis'),
                         'source_files':manifest.get('source_files'),
                         'canonical_source_sha256':manifest.get('canonical_source_sha256'),
                         'layout':manifest.get('layout'), 'ready_pose':manifest.get('ready_pose'),
                         'robot_attachment_frames':manifest.get('robot_attachment_frames'),
                         'build_args':manifest.get('build_args'),
                         'derived_from_manifest_sha256':manifest.get('derived_from_manifest_sha256')}
            _validate_asset_binding(candidate, asset, workcell)
            for record in candidate['source_files']:
                source = (root / record['path']).resolve()
                if not source.is_relative_to(root) or not source.is_file():
                    raise WorkcellValidationError('asset source outside root or missing')
                if hashlib.sha256(source.read_bytes()).hexdigest() != record['sha256']:
                    raise WorkcellValidationError('asset modeling source checksum mismatch')
            catalog['assets'][workcell] = candidate
    return catalog


def _selection(catalog, task_ids, targets, workcell):
    if workcell is not None and workcell not in catalog['assets']:
        raise WorkcellValidationError('unknown workcell')
    if task_ids is None:
        task_ids = [key for key, task in catalog['tasks'].items()
                    if workcell is None or task['workcell_id'] == workcell]
    if type(task_ids) is not list or not task_ids or any(type(t) is not str for t in task_ids):
        raise WorkcellValidationError('task_ids must be a nonempty list of task IDs')
    if len(set(task_ids)) != len(task_ids) or any(t not in catalog['tasks'] for t in task_ids):
        raise WorkcellValidationError('duplicate or unknown task ID')
    if workcell and any(catalog['tasks'][t]['workcell_id'] != workcell for t in task_ids):
        raise WorkcellValidationError('task does not belong to selected workcell')
    targets = {} if targets is None else targets
    if type(targets) is not dict or set(targets) - set(task_ids):
        raise WorkcellValidationError('targets must map selected task IDs to target lists')
    selected = {}
    for task_id in sorted(task_ids):
        ids = targets.get(task_id, catalog['tasks'][task_id]['target_ids'])
        if type(ids) is not list or not ids or any(type(t) is not str for t in ids):
            raise WorkcellValidationError('nonempty target lists required')
        if len(set(ids)) != len(ids) or set(ids) - set(catalog['tasks'][task_id]['target_ids']):
            raise WorkcellValidationError('duplicate or unknown target ID')
        selected[task_id] = sorted(ids)
    return selected


def _initial(task, seed, task_id, target_id, repeat):
    # Geometric reset parameters only: a seed identifies a repeat, it does not
    # fabricate contact forces or pretend to randomize unimplemented assets.
    return deepcopy(task['initial_state'])


def _episode(catalog, task_id, target_id, repeat, seed):
    task = catalog['tasks'][task_id]
    asset = catalog['assets'][task['workcell_id']]
    _sha(asset['manifest_sha256'], 'asset manifest SHA256')
    spec = {'task_id': task_id, 'target_id': target_id, 'workcell_id': task['workcell_id'],
            'repeat_index': repeat, 'seed': seed, 'kind': task['kind'],
            'initial_state': _initial(task, seed, task_id, target_id, repeat),
            'initial_validation': deepcopy(task['initial_validation']),
            'reset_frame': task.get('reset_frame', 'target'),
            'thresholds': deepcopy(task['thresholds']), 'goal_frame': task['goal_frame'],
            'semantic_bindings': deepcopy(asset['semantic_targets'][target_id]),
            'asset_manifest_sha256': asset['manifest_sha256'],
            'asset_provenance': {key:deepcopy(asset[key]) for key in ('canonical_source_sha256','build_args','derived_from_manifest_sha256')},
            'language_prompt': workcell_prompt(task_id, target_id),
            'protocol': deepcopy(catalog['protocol'])}
    return {'episode_id': f'{task_id}/{target_id}/{repeat:04d}/{seed}',
            'task_id': task_id, 'target_id': target_id, 'workcell_id': task['workcell_id'],
            'repeat_index': repeat, 'seed': seed, 'spec_hash': _digest(spec), 'spec': spec}


def make_workcell_plan(task_ids=None, *, repeats=1, seed=0, targets=None,
                       workcell=None, asset_root=None):
    """Expand each selected target ``repeats`` times; default is 29 variants.

    The plan binds SI thresholds, initial state, target semantics and asset
    manifest bytes. It is an adapter contract, not a successful rollout.
    """
    if type(repeats) is not int or not 1 <= repeats <= 100000:
        raise WorkcellValidationError('repeats must be an integer in 1..100000')
    if type(seed) is not int or not 0 <= seed < 2**64:
        raise WorkcellValidationError('seed must be uint64')
    catalog = workcell_catalog(asset_root)
    return _plan_from_catalog(catalog, task_ids, repeats, seed, targets, workcell)


def _plan_from_catalog(catalog, task_ids, repeats, seed, targets, workcell=None):
    selected = _selection(catalog, task_ids, targets, workcell)
    episodes = [_episode(catalog, task_id, target, repeat, seed)
                for task_id, ids in selected.items() for target in ids for repeat in range(repeats)]
    return {'schema': 'astrobench.workcell-plan/v2', 'seed': seed, 'repeats': repeats,
            'selection': selected, 'catalog_sha256': _digest(catalog),
            'asset_bindings': deepcopy(catalog['assets']), 'episodes': episodes}


def validate_workcell_plan(plan, *, asset_root=None):
    """Reject altered thresholds/initial states, dropped variants and bad hashes."""
    _finite_json(plan, 'plan')
    if type(plan) is not dict or plan.get('schema') != 'astrobench.workcell-plan/v2':
        raise WorkcellValidationError('astrobench.workcell-plan/v2 required; regenerate legacy plans to bind language prompts')
    try:
        if type(plan['repeats']) is not int or not 1 <= plan['repeats'] <= 100000:
            raise WorkcellValidationError('invalid repeat count')
        if type(plan['seed']) is not int or not 0 <= plan['seed'] < 2**64:
            raise WorkcellValidationError('invalid seed')
        catalog = workcell_catalog(asset_root) if asset_root is not None else _catalog_with_bindings(plan['asset_bindings'])
        expected = _plan_from_catalog(catalog,list(plan['selection']),plan['repeats'],plan['seed'],plan['selection'])
    except (KeyError, TypeError) as exc:
        raise WorkcellValidationError('invalid plan structure') from exc
    if _digest(plan) != _digest(expected):
        raise WorkcellValidationError('plan differs from canonical task/target/seed expansion')
    return plan


def _validate_episode(ep):
    _finite_json(ep, 'episode')
    if type(ep) is not dict:
        raise WorkcellValidationError('episode object required')
    try:
        catalog = workcell_catalog()
        task = catalog['tasks'][ep['task_id']]
        if ep['target_id'] not in task['target_ids']:
            raise WorkcellValidationError('unknown task target')
        if type(ep['seed']) is not int or not 0 <= ep['seed'] < 2**64:
            raise WorkcellValidationError('seed must be uint64')
        if type(ep['repeat_index']) is not int or ep['repeat_index'] < 0:
            raise WorkcellValidationError('repeat index must be a nonnegative integer')
        workcell = task['workcell_id']
        canonical = deepcopy(catalog['assets'][workcell])
        declared = ep['spec']['asset_provenance']
        if type(declared) is not dict or set(declared) != {'canonical_source_sha256','build_args','derived_from_manifest_sha256'}:
            raise WorkcellValidationError('exact asset provenance fields required')
        bound = deepcopy(canonical)
        bound.update(declared)
        bound['manifest_sha256'] = ep['spec']['asset_manifest_sha256']
        if bound['manifest_sha256'] != canonical['manifest_sha256']:
            bound['semantic_targets'] = _variant_targets(canonical,workcell,bound['build_args'])
        _validate_asset_binding(bound,canonical,workcell)
        catalog['assets'][workcell] = bound
        expected = _episode(catalog, ep['task_id'], ep['target_id'], ep['repeat_index'], ep['seed'])
    except (KeyError, TypeError) as exc:
        raise WorkcellValidationError('invalid episode structure') from exc
    if _digest(ep) != _digest(expected):
        raise WorkcellValidationError('episode differs from canonical contract')
    return task


def workcell_trace_fields(task_id):
    """Return measurement fields and units, for adapter authors and CLI help.

    Vectors are expressed in the named task goal/adapter frame; angular values
    are radians, including signed accumulated fastener angle (not modulo 2pi).
    Geometry margins are measured signed distances of the whole card mesh,
    not the card center or a policy's containment prediction. Latch booleans
    are measured joint/geometry states, never actuator commands.
    """
    cat = workcell_catalog()
    if task_id not in cat['tasks']:
        raise WorkcellValidationError('unknown task ID')
    state = cat['tasks'][task_id]['measurement_template']
    result = {key: ('bool' if type(v) is bool else f'vector[{len(v)}]' if type(v) is list else 'number')
              for key, v in state.items()}
    result.update(t_s='number', measurement_time_s='number', target_id='string',
                  linear_velocity_m_s='vector[3]', angular_velocity_rad_s='vector[3]',
                  forbidden_contact='bool', escaped='bool')
    return result


def _validate_evaluated_asset(ep, evaluated):
    """Validate target selection while preserving a canonical episode identity."""
    keys = {'evaluated_asset_manifest_sha256', 'evaluated_binding',
            'evaluated_asset_provenance'}
    if type(evaluated) is not dict or set(evaluated) != keys:
        raise WorkcellValidationError('exact evaluated asset fields required')
    if all(value is None for value in evaluated.values()):
        return
    if any(value is None for value in evaluated.values()):
        raise WorkcellValidationError('evaluated asset identity must be complete')
    catalog = workcell_catalog()
    canonical = catalog['assets'][ep['workcell_id']]
    provenance = evaluated['evaluated_asset_provenance']
    if type(provenance) is not dict or set(provenance) != {'canonical_source_sha256','build_args','derived_from_manifest_sha256'}:
        raise WorkcellValidationError('exact evaluated asset provenance fields required')
    asset = deepcopy(canonical)
    asset.update(provenance)
    asset['manifest_sha256'] = evaluated['evaluated_asset_manifest_sha256']
    if asset['manifest_sha256'] != canonical['manifest_sha256']:
        asset['semantic_targets'] = _variant_targets(canonical,ep['workcell_id'],asset['build_args'])
    _validate_asset_binding(asset,canonical,ep['workcell_id'])
    expected = asset['semantic_targets'][ep['target_id']]
    if _digest(expected) != _digest(evaluated['evaluated_binding']):
        raise WorkcellValidationError('evaluated target binding differs from allowed selection')
    # MELFI boxes are always independently addressable; RRM exports identify
    # the actual articulated SMA/captive target, with other targets static.
    if expected.get('active',True) is not True:
        raise WorkcellValidationError('evaluated target is not active in this asset')
    if provenance['canonical_source_sha256'] != ep['spec']['asset_provenance']['canonical_source_sha256']:
        raise WorkcellValidationError('evaluated asset source differs from planned source')


def resolve_workcell_episode(episode, asset_root):
    """Bind an episode to verified asset bytes, including allowed target builds.

    A canonical all-target plan remains the experiment identity. The returned
    fields identify the actual exported target selected for this episode;
    only variants built from the pinned modeling source are accepted.
    """
    _validate_episode(episode)
    if asset_root is None:
        raise WorkcellValidationError('explicit asset_root required for resolution')
    catalog = workcell_catalog(asset_root)
    asset = catalog['assets'][episode['workcell_id']]
    resolved = {
        'evaluated_asset_manifest_sha256': asset['manifest_sha256'],
        'evaluated_binding': deepcopy(asset['semantic_targets'][episode['target_id']]),
        'evaluated_asset_provenance': {key:deepcopy(asset[key]) for key in
            ('canonical_source_sha256','build_args','derived_from_manifest_sha256')},
    }
    _validate_evaluated_asset(episode,resolved)
    return resolved


def _sample(sample, episode, previous, fields):
    if type(sample) is not dict or set(sample) != set(fields):
        raise WorkcellValidationError('exact synchronized trace fields required')
    _finite_json(sample, 'sample')
    if sample['target_id'] != episode['target_id'] or type(sample['target_id']) is not str:
        raise WorkcellValidationError('sample target identity mismatch')
    for key, kind in fields.items():
        value = sample[key]
        if kind == 'bool' and type(value) is not bool:
            raise WorkcellValidationError(f'{key}: measured boolean required')
        elif kind == 'number':
            _number(value, key)
        elif kind.startswith('vector'):
            _vector(value, int(kind[7:-1]), key)
        if 'quat_wxyz' in key:
            _quaternion(value, key)
        if key.endswith('_force_n') or key in ('gripper_aperture_m', 'driver_clearance_m'):
            _number(value, key, 0)
    t = _number(sample['t_s'], 't_s', 0)
    if sample['measurement_time_s'] != t:
        raise WorkcellValidationError('all states must share the sample timestamp')
    p = episode['spec']['protocol']
    if t > p['horizon_s'] + 1e-9:
        raise WorkcellValidationError('trace exceeds registered horizon')
    if previous is None:
        if t != 0.:
            raise WorkcellValidationError('trace must start at t=0')
        validation = episode['spec']['initial_validation']
        for key, expected in episode['spec']['initial_state'].items():
            actual = sample[key]
            tolerance = validation['angle_tolerance_rad'] if 'angle' in key else validation['position_tolerance_m']
            if key == 'fastener_axial_m': tolerance = validation['fastener_axial_tolerance_m']
            if type(expected) is bool:
                equal = actual is expected
            elif 'quat_wxyz' in key:
                equal = 2*math.acos(min(1., abs(sum(a*b for a,b in zip(actual, expected))))) <= validation['angle_tolerance_rad']
            elif type(expected) is list:
                equal = math.dist(actual, expected) <= tolerance
            else:
                equal = abs(actual-expected) <= tolerance
            if not equal:
                raise WorkcellValidationError(f'initial state mismatch: {key}')
        for key, bounds in validation['ranges'].items():
            if not bounds[0] <= sample[key] <= bounds[1]:
                raise WorkcellValidationError(f'initial measurement outside range: {key}')
        if _norm(sample['linear_velocity_m_s']) > validation['max_linear_speed_m_s'] or _norm(sample['angular_velocity_rad_s']) > validation['max_angular_speed_rad_s']:
            raise WorkcellValidationError('initial motion exceeds registered range')
        if sample['forbidden_contact'] or sample['escaped']:
            raise WorkcellValidationError('invalid contact or escape at reset')
    else:
        dt = t - previous['t_s']
        if not 0 < dt <= p['max_sample_gap_s'] + 1e-9:
            raise WorkcellValidationError('timestamps not increasing or sample interval missing')
        # Reject teleport-sized discontinuities inconsistent with the bounded
        # workcell motion envelope. This is a sampling plausibility check.
        for key in ('goal_relative_position_m', 'adapter_goal_position_m', 'cap_adapter_position_m'):
            if key in sample and math.dist(sample[key], previous[key]) > .5*dt + .001:
                raise WorkcellValidationError(f'discontinuous measured pose: {key}')
        for key in ('lid_angle_rad', 'fastener_angle_rad'):
            if key in sample and abs(sample[key]-previous[key]) > 20.*dt + .02:
                raise WorkcellValidationError(f'discontinuous measured angle: {key}')
        if 'fastener_axial_m' in sample and abs(sample['fastener_axial_m']-previous['fastener_axial_m']) > .5*dt + .001:
            raise WorkcellValidationError('discontinuous measured axial position')
    return sample


def _conditions(s, ep, progress):
    task_id, p = ep['task_id'], ep['spec']['thresholds']
    checks = {'linear_speed': _norm(s['linear_velocity_m_s']) <= p['max_linear_speed_m_s'],
              'angular_speed': _norm(s['angular_velocity_rad_s']) <= p['max_angular_speed_rad_s'],
              'no_forbidden_contact': not s['forbidden_contact'], 'not_escaped': not s['escaped']}
    kind = ep['spec']['kind']
    if kind == 'card':
        grasped = (s['gripper_target_contact_force_n'] >= p['min_grasp_contact_force_n']
                   and s['gripper_aperture_m'] <= p['grasp_max_aperture_m'] and not s['object_released'])
        checks.update(position=_norm(s['goal_relative_position_m']) <= p['position_tolerance_m'],
                      orientation=_angle(s['goal_relative_quat_wxyz']) <= p['orientation_tolerance_rad'])
        progress['grasped'] |= grasped
        progress['reached_goal'] |= checks['position'] and checks['orientation']
        if task_id == 'card_insert':
            contained = s['min_containment_margin_m'] >= p['min_containment_margin_m']
            progress['contained'] |= contained and checks['position']
            checks.update(contained=contained, released=s['object_released'],
                          hand_open=s['gripper_aperture_m'] >= p['released_min_aperture_m'],
                          retained=s['retention_force_n'] >= p['min_retention_force_n'])
        else:
            checks['held'] = grasped
            if task_id == 'card_extract':
                checks['clear_of_opening'] = s['opening_clearance_m'] >= p['min_extraction_clearance_m']
                progress['extracted'] |= checks['clear_of_opening']
    elif kind == 'lid':
        if task_id == 'lid_open':
            checks['lid_open'] = s['lid_angle_rad'] >= p['open_min_angle_rad']
            checks['unlatched'] = not s['lid_latch_closed'] and not s['lid_latch_engaged']
        else:
            checks.update(lid_closed=abs(s['lid_angle_rad']) <= p['closed_max_angle_rad'],
                          latch_closed=s['lid_latch_closed'], latch_engaged=s['lid_latch_engaged'],
                          hand_clear=s['driver_clearance_m'] >= p['min_driver_clearance_m'])
        progress['lid_moved'] |= abs(s['lid_angle_rad']-ep['spec']['initial_state']['lid_angle_rad']) >= .05
    elif kind == 'cap':
        retained = (s['cap_retention_force_n'] >= p['min_retention_force_n']
                    and _norm(s['cap_adapter_position_m']) <= p['cap_position_tolerance_m']
                    and _angle(s['cap_adapter_quat_wxyz']) <= p['cap_orientation_tolerance_rad']
                    and _norm(s['cap_adapter_linear_velocity_m_s']) <= p['max_cap_relative_linear_speed_m_s']
                    and _norm(s['cap_adapter_angular_velocity_rad_s']) <= p['max_cap_relative_angular_speed_rad_s'])
        progress['captured'] |= retained
        progress['driver_engaged'] |= s['driver_attached'] and retained
        released = (not s['thread_engaged'] and s['fastener_angle_rad'] >= 2*math.pi*p['release_turns']
                    and s['fastener_axial_m'] >= p['thread_release_travel_m'])
        progress['unthreaded'] |= released and retained and progress['driver_engaged']
        progress['extracted'] |= (progress['unthreaded'] and retained
                                 and s['fastener_axial_m'] >= p['min_withdrawal_m'])
        docked = (_norm(s['adapter_goal_position_m']) <= p['stow_position_tolerance_m']
                  and _angle(s['adapter_goal_quat_wxyz']) <= p['stow_orientation_tolerance_rad'])
        supported = s['receiver_support_force_n'] >= p['min_support_force_n']
        latched = (all(abs(x) <= p['latch_closed_tolerance_m'] for x in s['receiver_latch_positions_m'])
                   and s['receiver_flange_captured'])
        progress['docked'] |= docked and supported and progress['extracted']
        progress['latched'] |= latched and progress['docked']
        checks.update(driver_engaged=progress['driver_engaged'], extracted=progress['extracted'], unthreaded=not s['thread_engaged'], retained=retained,
                      docked=docked, supported=supported, latched=latched,
                      driver_detached=not s['driver_attached'],
                      driver_clear=s['driver_clearance_m'] > p['min_driver_clearance_m'])
    else:
        checks['captive'] = not s['object_released']
        z, theta = s['fastener_axial_m'], s['fastener_angle_rad']
        checks['within_travel'] = -.00015 <= z <= p['max_travel_m']
        if task_id == 'captive_loosen':
            checks.update(turned=theta >= p['loosen_min_turns']*2*math.pi,
                          axial_travel=z >= p['loosen_min_travel_m'])
        else:
            checks.update(tight_angle=abs(theta) <= p['tight_max_angle_rad'],
                          seated=abs(z) <= p['tight_max_travel_m'],
                          driver_detached=not s['driver_attached'],
                          driver_clear=s['driver_clearance_m'] >= p['min_driver_clearance_m'])
        progress['fastener_moved'] |= s['driver_attached'] and abs(theta-ep['spec']['initial_state']['fastener_angle_rad']) >= .1
        checks['driven_motion'] = progress['fastener_moved']
    return checks


def _result(ep, status, success, progress, reasons, hold, samples, evaluated):
    result = {key: deepcopy(ep[key]) for key in ('episode_id','task_id','target_id','workcell_id','repeat_index','seed','spec_hash')}
    result.update(schema='astrobench.workcell-result/v1', judge=ep['spec']['protocol']['version'],
                  status=status, strict_success=success, progress=progress,
                  failure_reasons=sorted(set(reasons)), terminal_hold_s=hold,
                  sample_count=len(samples) if type(samples) is list else 0,
                  trace_sha256=None)
    result.update(deepcopy(evaluated))
    try:
        result['trace_sha256'] = _digest(samples)
    except WorkcellValidationError:
        pass
    result['result_sha256'] = _digest(result)
    return result


def score_workcell_trace(episode, samples, *, asset_root=None):
    """Judge a full 30-second synchronized trace; malformed traces are invalid.

    Returns status='completed' with success/failure for measured task outcomes;
    status='invalid', strict_success=None for missing/nonfinite samples or an
    already-completed/wrong initial state. Invalid plans raise ValueError.
    With asset_root, verify the actual active target export while retaining
    the plan's episode/spec identity, allowing all-target result aggregation.
    Without asset_root, asset evidence is null: this is measurement-only
    contract scoring and does not establish which asset bytes were loaded.
    """
    _validate_episode(episode)
    evaluated = (resolve_workcell_episode(episode,asset_root) if asset_root is not None else
                 dict.fromkeys(('evaluated_asset_manifest_sha256','evaluated_binding',
                                'evaluated_asset_provenance')))
    progress = dict.fromkeys(('grasped','reached_goal','contained','captured','unthreaded','extracted',
                              'docked','latched','lid_moved','fastener_moved','driver_engaged'), False)
    terminal_start, previous, checks = None, None, {}
    fatal = set()
    p = episode['spec']['protocol']
    fields = workcell_trace_fields(episode['task_id'])
    try:
        if type(samples) is not list or not samples:
            raise WorkcellValidationError('nonempty sample list required')
        for raw in samples:
            s = _sample(raw, episode, previous, fields)
            checks = _conditions(s, episode, progress)
            if s['forbidden_contact']: fatal.add('forbidden_contact')
            if s['escaped']: fatal.add('target_escaped')
            if episode['spec']['kind'] == 'cap':
                thresholds = episode['spec']['thresholds']
                if not s['thread_engaged'] and not progress['unthreaded']:
                    fatal.add('thread_released_without_driven_unscrewing')
                if progress['unthreaded'] and (s['cap_retention_force_n'] < thresholds['min_retention_force_n'] or _norm(s['cap_adapter_position_m']) > thresholds['cap_position_tolerance_m']):
                    fatal.add('cap_retention_lost')
                if previous and previous['driver_attached'] and not s['driver_attached'] and not progress['latched']:
                    fatal.add('driver_detached_before_receiver_lock')
            if episode['spec']['kind'] == 'captive' and (s['object_released'] or not checks['within_travel']):
                fatal.add('captive_retention_lost')
            if all(checks.values()):
                if terminal_start is None: terminal_start = s['t_s']
            else:
                terminal_start = None
            previous = s
        if abs(previous['t_s']-p['horizon_s']) > 1e-9:
            raise WorkcellValidationError('incomplete trace: full horizon required')
    except (WorkcellValidationError, KeyError, TypeError) as exc:
        return _result(episode, 'invalid', None, progress, [str(exc)], 0., samples, evaluated)
    hold = previous['t_s']-terminal_start if terminal_start is not None else 0.
    reasons = [key for key, passed in checks.items() if not passed] + sorted(fatal)
    if hold + 1e-9 < p['terminal_hold_s']:
        reasons.append('terminal_hold_incomplete')
    return _result(episode, 'completed', not reasons, progress, reasons, hold, samples, evaluated)


def aggregate_workcell_results(plan, results):
    """Keep all planned episodes, including invalid, runtime-error and not-run.

    A full-plan rate is withheld until every episode is a valid completed
    outcome. A separate success/planned coverage ratio never hides missing work.
    """
    validate_workcell_plan(plan)
    _finite_json(results, 'results')
    if type(results) is not list:
        raise WorkcellValidationError('results list required')
    by_id = {ep['episode_id']: ep for ep in plan['episodes']}
    incoming = {}
    for result in results:
        if type(result) is not dict or result.get('episode_id') not in by_id:
            raise WorkcellValidationError('unknown result episode')
        ident = result['episode_id']
        if ident in incoming:
            raise WorkcellValidationError('duplicate result episode')
        ep = by_id[ident]
        for field in ('task_id','target_id','workcell_id','repeat_index','seed','spec_hash'):
            if type(result.get(field)) is not type(ep[field]) or result.get(field) != ep[field]:
                raise WorkcellValidationError(f'result identity mismatch: {field}')
        status, strict = result.get('status'), result.get('strict_success')
        if status not in ('completed','invalid','runtime_error'):
            raise WorkcellValidationError('unsupported result status')
        if status == 'completed' and type(strict) is not bool:
            raise WorkcellValidationError('completed result requires boolean success')
        if status != 'completed' and strict is not None:
            raise WorkcellValidationError('invalid/error result cannot claim a task outcome')
        reasons = result.get('failure_reasons')
        if type(reasons) is not list or any(type(reason) is not str or not reason for reason in reasons):
            raise WorkcellValidationError('failure_reasons must be a list of nonempty strings')
        if status != 'completed' and not reasons:
            raise WorkcellValidationError('invalid/error result requires a concrete reason')
        if status in ('completed','invalid'):
            required = {'episode_id','task_id','target_id','workcell_id','repeat_index','seed','spec_hash',
                        'schema','judge','status','strict_success','progress','failure_reasons',
                        'terminal_hold_s','sample_count','trace_sha256','result_sha256',
                        'evaluated_asset_manifest_sha256','evaluated_binding','evaluated_asset_provenance'}
            if set(result) != required or result['schema'] != 'astrobench.workcell-result/v1':
                raise WorkcellValidationError('exact scored result schema required')
            _validate_evaluated_asset(ep, {key:result[key] for key in
                ('evaluated_asset_manifest_sha256','evaluated_binding','evaluated_asset_provenance')})
            progress_keys = {'grasped','reached_goal','contained','captured','unthreaded','extracted',
                             'docked','latched','lid_moved','fastener_moved','driver_engaged'}
            if type(result['progress']) is not dict or set(result['progress']) != progress_keys or any(type(x) is not bool for x in result['progress'].values()):
                raise WorkcellValidationError('typed measured progress fields required')
            if type(result['sample_count']) is not int or result['sample_count'] < 0:
                raise WorkcellValidationError('sample_count must be a nonnegative integer')
            hold = _number(result['terminal_hold_s'],'terminal hold',0)
            if hold > ep['spec']['protocol']['horizon_s']:
                raise WorkcellValidationError('terminal hold exceeds horizon')
            expected_hash = result.get('result_sha256')
            unsigned = {k:v for k,v in result.items() if k != 'result_sha256'}
            if expected_hash != _digest(unsigned) or result.get('judge') != ep['spec']['protocol']['version']:
                raise WorkcellValidationError('result checksum/judge mismatch')
            if status == 'completed':
                if result['sample_count'] < math.ceil(ep['spec']['protocol']['horizon_s']/ep['spec']['protocol']['max_sample_gap_s'])+1:
                    raise WorkcellValidationError('completed result has insufficient samples')
                if not strict and not reasons:
                    raise WorkcellValidationError('failed result requires a reason')
                _sha(result.get('trace_sha256'), 'trace checksum')
                _number(result.get('terminal_hold_s'), 'terminal hold', 0)
                if strict and result['terminal_hold_s'] + 1e-9 < ep['spec']['protocol']['terminal_hold_s']:
                    raise WorkcellValidationError('success without terminal hold')
                if strict and result.get('failure_reasons') != []:
                    raise WorkcellValidationError('success with failure reasons')
        incoming[ident] = result

    def counts(episodes):
        statuses = Counter(incoming[ep['episode_id']]['status'] if ep['episode_id'] in incoming else 'not_run'
                           for ep in episodes)
        completed = statuses['completed']
        success = sum(incoming.get(ep['episode_id'], {}).get('strict_success') is True for ep in episodes)
        n = len(episodes)
        return {'planned': n, 'completed': completed, 'success': success,
                'failed': completed-success, 'invalid': statuses['invalid'],
                'runtime_errors': statuses['runtime_error'], 'not_run': statuses['not_run'],
                'observed_success_rate': success/completed if completed else None,
                'observed_rate_denominator': completed,
                'observed_wilson95': wilson95(success, completed),
                'success_fraction_of_plan': success/n,
                'planned_denominator': n,
                'full_plan_success_rate': success/n if completed == n else None,
                'complete': completed == n,
                'not_run_episode_ids': [ep['episode_id'] for ep in episodes if ep['episode_id'] not in incoming]}

    groups = defaultdict(list)
    for ep in plan['episodes']:
        groups[(ep['task_id'],ep['target_id'])].append(ep)
    task_groups = defaultdict(list)
    for ep in plan['episodes']: task_groups[ep['task_id']].append(ep)
    reasons = Counter(reason for result in results for reason in result.get('failure_reasons', []))
    return {'schema': 'astrobench.workcell-report/v1', 'plan_sha256': _digest(plan),
            'overall': counts(plan['episodes']),
            'by_task': [dict(task_id=task, **counts(eps)) for task,eps in sorted(task_groups.items())],
            'by_task_target': [dict(task_id=key[0],target_id=key[1],**counts(eps)) for key,eps in sorted(groups.items())],
            'failure_reasons': dict(sorted(reasons.items()))}
