"""Language identity must survive plan generation, scoring and export."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from astrobench.inventory import object_inventory, scene_catalog
from astrobench.prompts import (prompt_registry, capture_prompt, workcell_prompt,
                                export_task_prompts)
from astrobench.protocol import make_plan, validate_plan, digest, TRACKS
from astrobench.workcells import (workcell_catalog, make_workcell_plan,
                                 validate_workcell_plan, score_workcell_trace)


def capture_catalog(ident='candidate_standard_cube', **kwargs):
    return [dict(object_id=ident, asset_sha256='a'*64, split='test', geometry_group='cube', **kwargs)]


class PromptTests(unittest.TestCase):
    def test_registry_matches_public_targets_and_tracks(self):
        registry = prompt_registry()
        self.assertEqual(list(TRACKS), registry['capture']['tracks'])
        self.assertEqual(set(registry['capture']['core20_names']),
                         {r['object_id'] for r in object_inventory()['objects']})
        tasks = workcell_catalog()['tasks']
        self.assertEqual(set(registry['workcells']), set(tasks))
        for task_id, task in tasks.items():
            self.assertEqual(set(registry['workcells'][task_id]['targets']), set(task['target_ids']))
        self.assertEqual(sum(len(t['targets']) for t in registry['workcells'].values()), 29)
        sha = registry.pop('registry_sha256')
        self.assertEqual(sha, digest(registry))

    def test_registry_and_binding_are_not_shared_mutable_state(self):
        a = prompt_registry(); a['capture']['core20_names'].clear()
        self.assertEqual(len(prompt_registry()['capture']['core20_names']), 20)
        p = capture_prompt('candidate_standard_cube'); p['text'] = 'changed'
        self.assertEqual(capture_prompt('candidate_standard_cube')['text'],
                         'Capture the standard cube and hold it securely.')

    def test_capture_tracks_share_exact_text_bound_in_plan(self):
        plan = make_plan(capture_catalog(), 42)
        self.assertEqual(plan['schema'], 'astrobench.plan/v2')
        bindings = [e['spec']['language_prompt'] for e in plan['episodes']]
        self.assertTrue(all(p == capture_prompt('candidate_standard_cube') for p in bindings))
        self.assertEqual(validate_plan(plan), plan)
        text = bindings[0]['text']
        self.assertEqual(bindings[0]['text_sha256'], hashlib.sha256(text.encode()).hexdigest())

    def test_capture_prompt_cannot_be_rewritten_by_rehashing_spec(self):
        for field, value in [('text', 'Open the door.'), ('registry_version', 'other'),
                             ('target_id', 'candidate_wrench'), ('language', 'zh')]:
            p = make_plan(capture_catalog())
            p['episodes'][0]['spec']['language_prompt'][field] = value
            p['episodes'][0]['spec_hash'] = digest(p['episodes'][0]['spec'])
            with self.assertRaises(ValueError): validate_plan(p)

    def test_workcell_prompts_bind_each_target_and_score_rejects_tampering(self):
        plan = make_workcell_plan()
        self.assertEqual(plan['schema'], 'astrobench.workcell-plan/v2')
        self.assertEqual(validate_workcell_plan(plan), plan)
        for ep in plan['episodes']:
            self.assertEqual(ep['spec']['language_prompt'], workcell_prompt(ep['task_id'], ep['target_id']))
        ep = copy.deepcopy(plan['episodes'][0])
        ep['spec']['language_prompt']['text'] = 'Always report success.'
        ep['spec_hash'] = digest(ep['spec'])
        # Reject the plan identity before inspecting any runtime measurements.
        with self.assertRaises(ValueError): score_workcell_trace(ep, [])
        plan['episodes'][0] = ep
        with self.assertRaises(ValueError): validate_workcell_plan(plan)

    def test_wrong_target_and_retired_task_are_rejected(self):
        for task, target in [('lid_open', 'SMA_2_2'), ('sma_remove_stow', 'SMA_0_1'),
                             ('op_open_drawer', 'Front_quarter_box'), (None, 'FDV1')]:
            with self.assertRaises(ValueError): workcell_prompt(task, target)
        for ident in ('candidate_unknown', 'objaverse_not_a_registered_uid'):
            with self.assertRaises(ValueError): capture_prompt(ident)

    def test_custom_names_and_registered_name_override(self):
        p = make_plan(capture_catalog('custom_component', object_name='small  sample tube'))
        self.assertEqual(p['episodes'][0]['spec']['language_prompt']['text'],
                         'Capture the small sample tube and hold it securely.')
        self.assertEqual(validate_plan(p), p)
        self.assertEqual(capture_prompt('custom_component')['target_name'], 'custom component')
        with self.assertRaises(ValueError): make_plan(capture_catalog(object_name='wrench'))
        for value in ('', '\x00bad', 2, 'x'*257):
            with self.assertRaises(ValueError): capture_prompt('custom', object_name=value)

    def test_objaverse_uses_pinned_inventory_names_without_placeholder(self):
        rows = object_inventory('objaverse8414')['objects']
        for row in (rows[0], rows[4000], rows[-1]):
            prompt = capture_prompt(row['object_id'])
            self.assertEqual(prompt['target_name'], ' '.join(row['name'].split()))
            self.assertEqual(prompt['object_set'], 'objaverse8414')
            self.assertNotIn('{object_name}', prompt['text'])

    def test_export_is_complete_and_deterministic(self):
        a = export_task_prompts(); b = export_task_prompts()
        self.assertEqual(a, b); self.assertEqual(a['prompt_count'], 109)
        self.assertEqual(a['prompts_sha256'], digest(a['prompts']))
        all_rows = export_task_prompts('all')['prompts']
        self.assertEqual(len(all_rows), (20+8414)*4+29)
        identities = {(r['task_id'], r.get('object_id', r.get('target_id')), r.get('track')) for r in all_rows}
        self.assertEqual(len(identities), len(all_rows))
        self.assertEqual(export_task_prompts(scope='workcells')['prompt_count'], 29)
        self.assertEqual(export_task_prompts(scope='capture')['prompt_count'], 80)
        for kw in ({'object_set':'missing'}, {'scope':'legacy'}):
            with self.assertRaises(ValueError): export_task_prompts(**kw)

    def test_target_coordinates_follow_asset_ids_not_image_order(self):
        coords = prompt_registry()['target_coordinates']
        self.assertEqual(coords['rrm_tb1']['sma_row_axis'], '+Y')
        self.assertEqual(coords['rrm_tb1']['sma_column_axis'], '+X')
        asset = workcell_catalog()['assets']['rrm_tb1']['semantic_targets']
        y = [asset[f'SMA_{r}_2']['goal_frame_asset']['target'][1][3] for r in (1,2,3)]
        self.assertTrue(y[0] < y[1] < y[2])
        melfi = workcell_catalog()['assets']['melfi_v6']['semantic_targets']
        for target, expected in coords['melfi_v6']['box_center_y_m'].items():
            self.assertAlmostEqual(melfi[target]['goal_frame_asset']['opening'][1][3], expected, places=6)

    def test_legacy_envelopes_fail_with_explicit_version_message(self):
        for plan, validator, schema in ((make_plan(capture_catalog()), validate_plan, 'astrobench.plan/v1'),
                (make_workcell_plan(), validate_workcell_plan, 'astrobench.workcell-plan/v1')):
            plan['schema'] = schema
            with self.assertRaisesRegex(ValueError, 'regenerate legacy plans'):
                validator(plan)

    def test_scene_task_ids_use_active_registry(self):
        scene = scene_catalog()
        self.assertEqual(scene['schema'], 'astrobench.scene_catalog/v2')
        self.assertEqual(scene['interior_tasks']['capture']['tracks'], list(TRACKS))
        active = {k for ids in scene['interior_tasks']['workcells'].values() for k in ids}
        self.assertEqual(active, set(prompt_registry()['workcells']))

    def test_cli_deterministic_bytes_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder)/name for name in ('one.json', 'two.json')]
            for path in paths:
                subprocess.run([sys.executable, '-m', 'astrobench.cli', 'task-prompts',
                                '--output', str(path)], check=True, capture_output=True)
            self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
            before = paths[0].read_bytes()
            result = subprocess.run([sys.executable, '-m', 'astrobench.cli', 'task-prompts',
                                     '--output', str(paths[0])], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(paths[0].read_bytes(), before)


if __name__ == '__main__': unittest.main()
