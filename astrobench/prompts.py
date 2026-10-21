"""Versioned language instructions shared by plans, adapters and documentation.

The registry defines current release wording. It is not an execution log.
Return values are independent copies so callers cannot mutate the registry.
"""
from copy import deepcopy
from functools import lru_cache
import hashlib
from importlib.resources import files
import json

from .inventory import object_inventory


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


@lru_cache(maxsize=1)
def _registry():
    return json.loads(files('astrobench').joinpath('data/task_prompts.json').read_text(encoding='utf-8'))


def prompt_registry():
    """Return the complete registry and its canonical JSON digest."""
    registry = deepcopy(_registry())
    return {**registry, 'registry_sha256': _digest(registry)}


def _label(value, name):
    if type(value) is not str:
        raise ValueError(f'{name}: nonempty text required')
    text = ' '.join(value.split())
    if not text or len(text) > 256 or any(ord(c) < 32 or ord(c) == 127 for c in text):
        raise ValueError(f'{name}: nonempty printable label of at most 256 characters required')
    return text


@lru_cache(maxsize=1)
def _objaverse_names():
    return {row['object_id']: _label(row['name'], 'object name')
            for row in object_inventory('objaverse8414')['objects']}


def _binding(task_id, target_id, target_name, text):
    registry = _registry()
    return {'registry_version': registry['version'], 'registry_sha256': _digest(registry),
            'language': registry['language'], 'task_id': task_id, 'target_id': target_id,
            'target_name': target_name, 'text': text,
            'text_sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}


def capture_prompt(object_id, *, object_name=None):
    """Resolve an inventory name or a custom label into the capture instruction.

    Registered identities cannot override their canonical label. An unknown
    ``candidate_`` or ``objaverse_`` identity is rejected instead of silently
    being treated as a custom object. Tracks intentionally share one wording.
    """
    if type(object_id) is not str or not object_id or object_id.strip() != object_id:
        raise ValueError('object_id: nonempty identity required')
    capture = _registry()['capture']
    if object_id in capture['core20_names']:
        name, object_set = capture['core20_names'][object_id], 'core20'
    elif object_id.startswith('objaverse_'):
        if object_id not in _objaverse_names():
            raise ValueError('unknown Objaverse object_id')
        name, object_set = _objaverse_names()[object_id], 'objaverse8414'
    elif object_id.startswith('candidate_'):
        raise ValueError('unknown core20 object_id')
    else:
        name, object_set = _label(object_name if object_name is not None else object_id.replace('_', ' '),
                                  'object_name'), 'custom'
    if object_set != 'custom' and object_name is not None and _label(object_name, 'object_name') != name:
        raise ValueError('registered object_name differs from canonical label')
    text = capture['template'].format(object_name=name)
    return {**_binding(capture['task_id'], object_id, name, text), 'object_set': object_set}


def workcell_prompt(task_id, target_id):
    """Resolve one of the 29 registered task/target instructions."""
    if type(task_id) is not str or task_id not in _registry()['workcells']:
        raise ValueError('unknown workcell task_id')
    task = _registry()['workcells'][task_id]
    if type(target_id) is not str or target_id not in task['targets']:
        raise ValueError('unknown target for workcell task')
    name = task['targets'][target_id]
    return _binding(task_id, target_id, name, task['template'].format(target_name=name))


def export_task_prompts(object_set='core20', *, scope='all'):
    """Deterministically expand capture tracks and/or all workcell targets.

    Exporting names does not create an asset catalog: capture planning also
    requires each object's geometry identity and split assignment.
    """
    if object_set not in ('core20', 'objaverse8414', 'all'):
        raise ValueError('unknown object_set')
    if scope not in ('all', 'capture', 'workcells'):
        raise ValueError('unknown prompt scope')
    rows = []
    if scope in ('all', 'capture'):
        sets = ('core20', 'objaverse8414') if object_set == 'all' else (object_set,)
        ids = sorted(row['object_id'] for selected in sets for row in object_inventory(selected)['objects'])
        for ident in ids:
            for track in _registry()['capture']['tracks']:
                rows.append({'task_id': 'capture_retain', 'object_id': ident, 'track': track,
                             'language_prompt': capture_prompt(ident)})
    if scope in ('all', 'workcells'):
        for task_id, task in sorted(_registry()['workcells'].items()):
            for target_id in sorted(task['targets']):
                rows.append({'task_id': task_id, 'workcell_id': task['workcell_id'],
                             'target_id': target_id,
                             'language_prompt': workcell_prompt(task_id, target_id)})
    registry = prompt_registry()
    return {'schema': 'astrobench.task-prompts/v1', 'registry_version': registry['version'],
            'registry_sha256': registry['registry_sha256'], 'object_set': object_set,
            'scope': scope, 'prompt_count': len(rows), 'prompts_sha256': _digest(rows),
            'prompts': rows}
