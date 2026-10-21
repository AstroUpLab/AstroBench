"""Adversarial contract tests use synthetic measurements, not task evidence."""
import copy
import hashlib
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from astrobench import workcells as w


def catalog_fixture():
    c = json.loads(Path(w.__file__).with_name('data').joinpath('workcells.json').read_text())
    for n, a in c['assets'].items():
        a['manifest_sha256'] = hashlib.sha256(n.encode()).hexdigest()
    return c


def episode(task='card_transfer_to_mouth'):
    return w.make_workcell_plan([task])['episodes'][0]


def linear(a, b, alpha):
    if isinstance(a, list): return [linear(x,y,alpha) for x,y in zip(a,b)]
    return a+(b-a)*max(0., min(1., alpha))


def trace(ep):
    """An ideal measured-state fixture with a full horizon and ordered stages."""
    task = w.workcell_catalog()['tasks'][ep['task_id']]
    result = []
    for i in range(1501):
        t = i/50
        s = copy.deepcopy(task['measurement_template'])
        s.update(ep['spec']['initial_state'])
        s.update(t_s=t, measurement_time_s=t, target_id=ep['target_id'],
                 linear_velocity_m_s=[0.,0.,0.], angular_velocity_rad_s=[0.,0.,0.],
                 forbidden_contact=False, escaped=False)
        kind, tid = task['kind'], ep['task_id']
        if kind == 'card':
            s['goal_relative_position_m'] = linear(ep['spec']['initial_state']['goal_relative_position_m'],[0.,0.,0.],t/10)
            if tid == 'card_insert':
                s['gripper_target_contact_force_n']=.1
                s['gripper_aperture_m']=.015 if t<20 else .06
                s['object_released']=t>=20
                s['min_containment_margin_m']=linear(-.05,.001,t/10)
                s['retention_force_n']=.1 if t>=20 else 0.
            else:
                s['gripper_target_contact_force_n']=.1 if t>=2 else 0.
                s['gripper_aperture_m']=.015 if t>=2 else .06
                s['object_released']=t<2
                if tid == 'card_extract':
                    s['min_containment_margin_m']=linear(.001,-.05,t/10)
                    s['opening_clearance_m']=linear(-.11,.10,t/10)
                    s['retention_force_n']=.1 if t<2 else 0.
        elif kind == 'lid':
            s['lid_angle_rad']=linear(ep['spec']['initial_state']['lid_angle_rad'],1.5 if tid=='lid_open' else 0.,max(0,t-1)/5)
            closed=t<1 if tid=='lid_open' else t>=7
            s['lid_latch_closed']=closed
            s['lid_latch_engaged']=closed
        elif kind == 'cap':
            s['cap_adapter_position_m']=linear([0.,0.,-.1],[0.,0.,0.],t/3)
            s['cap_retention_force_n']=.1 if t>=3 else 0.
            s['driver_attached']=t<24
            s['fastener_angle_rad']=linear(0.,4*math.pi,max(0,t-4)/6)
            release=task['thresholds']['thread_release_travel_m']
            s['fastener_axial_m']=linear(0.,release,max(0,t-4)/6) if t<10 else linear(release,task['thresholds']['min_withdrawal_m']+.005,(t-10)/5)
            s['thread_engaged']=t<10
            s['adapter_goal_position_m']=linear([.15,0.,.1],[0.,0.,0.],max(0,t-15)/7)
            s['receiver_support_force_n']=.1 if t>=22 else 0.
            s['receiver_latch_positions_m']=[0.,0.] if t>=23 else [.004,.004]
            s['receiver_flange_captured']=t>=23
            s['driver_clearance_m']=.11 if t>=25 else 0.
        else:
            goal_angle,goal_z=(6*math.pi,.0021) if tid=='captive_loosen' else (0.,0.)
            s['fastener_angle_rad']=linear(ep['spec']['initial_state']['fastener_angle_rad'],goal_angle,max(0,t-1)/7)
            s['fastener_axial_m']=linear(ep['spec']['initial_state']['fastener_axial_m'],goal_z,max(0,t-1)/7)
            s['driver_attached']=1<=t<10
        result.append(s)
    return result


class WorkcellTests(unittest.TestCase):
    def setUp(self):
        c = catalog_fixture()
        self.mock = patch.object(w, '_base_catalog', side_effect=lambda: copy.deepcopy(c))
        self.mock.start()
        self.addCleanup(self.mock.stop)

    def test_full_expansion_and_determinism(self):
        p = w.make_workcell_plan(repeats=2,seed=7)
        self.assertEqual(len(p['episodes']),58)
        self.assertEqual(p,w.make_workcell_plan(repeats=2,seed=7))
        self.assertEqual(w.validate_workcell_plan(p),p)
        self.assertEqual(len(w.make_workcell_plan(workcell='melfi_v6')['episodes']),15)
        self.assertEqual(len(w.make_workcell_plan(workcell='rrm_tb1')['episodes']),14)

    def test_unknown_duplicate_and_wrong_types(self):
        for kw in ({'task_ids':['unknown']},{'repeats':True},{'seed':1.0},{'seed':-1},
                   {'targets':{'lid_open':['wrong']}},{'task_ids':['lid_open','lid_open']},
                   {'task_ids':['lid_open'],'workcell':'rrm_tb1'},
                   {'task_ids':['lid_open'],'targets':{'lid_open':['Front_quarter_box']*2}}):
            with self.assertRaises(ValueError): w.make_workcell_plan(**kw)

    def test_plan_hash_does_not_authorize_threshold_or_initial_changes(self):
        for kind in ('threshold','initial','drop','target'):
            p=w.make_workcell_plan(['lid_open'])
            e=p['episodes'][0]
            if kind=='threshold':e['spec']['thresholds']['open_min_angle_rad']=0.
            elif kind=='initial':e['spec']['initial_state']['lid_angle_rad']=1.5
            elif kind=='target':e['target_id']='wrong'
            else:p['episodes'].pop()
            e['spec_hash']=w._digest(e['spec'])
            with self.assertRaises(ValueError): w.validate_workcell_plan(p)

    def test_all_nine_valid_measured_outcomes(self):
        for tid in w.workcell_catalog()['tasks']:
            with self.subTest(tid=tid):
                e=episode(tid);result=w.score_workcell_trace(e,trace(e))
                self.assertEqual(result['status'],'completed',result)
                self.assertTrue(result['strict_success'],result)
                self.assertGreaterEqual(result['terminal_hold_s'],1.)

    def test_incomplete_unsynchronized_nan_and_boolean_numbers_invalid(self):
        e=episode();data=trace(e)
        bads=[data[1:],data[:-1],data[:20]+data[22:]]
        for key,value in [('t_s',float('nan')),('measurement_time_s',9.),
                          ('target_id','other'),('forbidden_contact',1),
                          ('gripper_aperture_m',True),('goal_relative_quat_wxyz',[0,0,0,0]),
                          ('goal_relative_position_m',[0.,float('inf'),0.])]:
            bad=copy.deepcopy(data);bad[300][key]=value;bads.append(bad)
        for bad in bads:
            r=w.score_workcell_trace(e,bad)
            self.assertEqual(r['status'],'invalid')
            self.assertIsNone(r['strict_success'])

    def test_policy_success_flag_is_not_a_measurement(self):
        e=episode();bad=trace(e)
        for s in bad:s['success']=True
        self.assertEqual(w.score_workcell_trace(e,bad)['status'],'invalid')

    def test_initial_done_cheating_invalid(self):
        for tid in ('lid_open','lid_close','card_insert','captive_loosen','captive_tighten','sma_remove_stow'):
            e=episode(tid);data=trace(e)
            for k in e['spec']['initial_state']:
                data[0][k]=copy.deepcopy(data[-1][k])
            self.assertEqual(w.score_workcell_trace(e,data)['status'],'invalid',tid)

    def test_force_initialization_is_range_not_exact_setpoint(self):
        e=episode('card_insert');data=trace(e)
        data[0]['gripper_target_contact_force_n']=.087
        self.assertTrue(w.score_workcell_trace(e,data)['strict_success'])
        data[0]['gripper_target_contact_force_n']=0.
        self.assertEqual(w.score_workcell_trace(e,data)['status'],'invalid')

    def test_mesh_based_opening_clearance_and_driver_reset(self):
        for tid in ('card_insert','card_transfer_to_mouth'):
            e=episode(tid);data=trace(e)
            if tid == 'card_insert':
                self.assertEqual(e['spec']['initial_state']['goal_relative_position_m'],[0.,0.,.1435])
            data[0]['opening_clearance_m']=.002
            self.assertTrue(w.score_workcell_trace(e,data)['strict_success'])
        e=episode('card_extract')
        self.assertEqual(e['spec']['initial_state']['goal_relative_position_m'],[0.,0.,-.1685])
        e=episode('fdv1_remove_stow');data=trace(e)
        self.assertTrue(data[0]['driver_attached'])
        self.assertEqual(data[0]['driver_clearance_m'],0.)
        data[0]['driver_attached']=False
        self.assertEqual(w.score_workcell_trace(e,data)['status'],'invalid')

    def test_grasp_is_not_insertion_or_extraction(self):
        for tid,key,value in [('card_insert','object_released',False),
                              ('card_insert','min_containment_margin_m',-.001),
                              ('card_insert','retention_force_n',0.),
                              ('card_extract','opening_clearance_m',-.01)]:
            e=episode(tid);data=trace(e)
            for s in data[1250:]:s[key]=value
            r=w.score_workcell_trace(e,data)
            self.assertEqual(r['status'],'completed')
            self.assertFalse(r['strict_success'])
            self.assertTrue(r['progress']['grasped'])

    def test_terminal_hold_and_late_release_failure(self):
        e=episode('lid_close');data=trace(e)
        for s in data[1451:]:s['lid_latch_engaged']=False
        r=w.score_workcell_trace(e,data)
        self.assertFalse(r['strict_success'])
        self.assertIn('latch_engaged',r['failure_reasons'])
        data=trace(e)
        for s in data[350:1451]:s['lid_latch_engaged']=False
        self.assertFalse(w.score_workcell_trace(e,data)['strict_success'])
        data[1450]['lid_latch_engaged']=True
        self.assertTrue(w.score_workcell_trace(e,data)['strict_success'])

    def test_cap_requires_receiver_and_driver_handoff(self):
        for key,value in [('receiver_flange_captured',False),('receiver_latch_positions_m',[.004,0.]),
                          ('driver_attached',True),('driver_clearance_m',.05),
                          ('receiver_support_force_n',0.)]:
            e=episode('fdv1_remove_stow');data=trace(e)
            for s in data[1200:]:s[key]=value
            r=w.score_workcell_trace(e,data)
            self.assertEqual(r['status'],'completed')
            self.assertFalse(r['strict_success'])

    def test_unscrewing_and_captive_motion_require_drive_engagement(self):
        for tid in ('sma_remove_stow','captive_loosen','captive_tighten'):
            e=episode(tid);data=trace(e)
            for s in data[1:]:s['driver_attached']=False
            r=w.score_workcell_trace(e,data)
            self.assertEqual(r['status'],'completed')
            self.assertFalse(r['strict_success'])

    def test_captive_retention_loss_cannot_be_erased(self):
        e=episode('captive_loosen');data=trace(e);data[400]['object_released']=True
        r=w.score_workcell_trace(e,data)
        self.assertFalse(r['strict_success'])
        self.assertIn('captive_retention_lost',r['failure_reasons'])

    def test_nonfinite_result_duplicate_missing_denominator_and_tamper(self):
        p=w.make_workcell_plan(['lid_open'],repeats=2)
        e=p['episodes'][0];good=w.score_workcell_trace(e,trace(e))
        report=w.aggregate_workcell_results(p,[good])['overall']
        self.assertEqual(report['planned'],6)
        self.assertEqual(report['not_run'],5)
        self.assertEqual(report['observed_rate_denominator'],1)
        self.assertEqual(report['success_fraction_of_plan'],1/6)
        self.assertIsNone(report['full_plan_success_rate'])
        self.assertFalse(report['complete'])
        for bads in ([good,good],[dict(good,strict_success=False)],[dict(good,seed=True)],
                     [dict(good,hidden=float('nan'))]):
            with self.assertRaises(ValueError):w.aggregate_workcell_results(p,bads)
        invalid=w.score_workcell_trace(p['episodes'][1],[])
        report=w.aggregate_workcell_results(p,[good,invalid])['overall']
        self.assertEqual(report['invalid'],1)
        self.assertEqual(report['completed'],1)
        self.assertEqual(report['not_run'],4)

    def test_allowed_target_variant_preserves_geometry_and_source(self):
        c=w.workcell_catalog(); canonical=copy.deepcopy(c['assets']['rrm_tb1'])
        variant=copy.deepcopy(canonical)
        variant.update(manifest_sha256='c'*64,derived_from_manifest_sha256=canonical['manifest_sha256'],
                       build_args={'sma_row':1,'sma_col':3,'captive_index':2})
        variant['semantic_targets']=w._variant_targets(canonical,'rrm_tb1',variant['build_args'])
        self.assertTrue(variant['semantic_targets']['SMA_1_3']['active'])
        self.assertTrue(variant['semantic_targets']['captive_2']['active'])
        self.assertFalse(variant['semantic_targets']['SMA_2_2']['active'])
        c['assets']['rrm_tb1']=variant
        plan=w._plan_from_catalog(c,['sma_remove_stow'],1,0,{'sma_remove_stow':['SMA_1_3']})
        w.validate_workcell_plan(plan)
        e=plan['episodes'][0]
        self.assertEqual(e['spec']['asset_manifest_sha256'],'c'*64)
        self.assertTrue(w.score_workcell_trace(e,trace(e))['strict_success'])
        for key in ('source','frame','unit','args','root'):
            broken=copy.deepcopy(plan)
            a=broken['asset_bindings']['rrm_tb1']
            if key=='source':a['canonical_source_sha256']='d'*64
            elif key=='unit':a['units']='cm'
            elif key=='args':a['build_args']['sma_row']=True
            elif key=='root':a['semantic_targets']['SMA_1_3']['root_object']='unrelated'
            else:a['semantic_targets']['SMA_1_3']['goal_frame_asset']['target'][0][3]+=1.
            with self.assertRaises(ValueError):w.validate_workcell_plan(broken)

    def test_canonical_all_target_plan_resolves_and_aggregates_variant(self):
        plan=w.make_workcell_plan()
        catalog=w.workcell_catalog();variant=copy.deepcopy(catalog)
        canonical=catalog['assets']['rrm_tb1'];a=variant['assets']['rrm_tb1']
        a.update(manifest_sha256='c'*64,derived_from_manifest_sha256=canonical['manifest_sha256'],
                 build_args={'sma_row':1,'sma_col':3,'captive_index':2})
        a['semantic_targets']=w._variant_targets(canonical,'rrm_tb1',a['build_args'])
        actual_catalog=w.workcell_catalog
        def selected(root=None):
            return copy.deepcopy(variant) if root is not None else actual_catalog()
        results=[]
        with patch.object(w,'workcell_catalog',side_effect=selected):
            for e in plan['episodes']:
                if e['target_id'] not in ('SMA_1_3','captive_2'):continue
                resolved=w.resolve_workcell_episode(e,'variant-root')
                self.assertTrue(resolved['evaluated_binding']['active'])
                r=w.score_workcell_trace(e,trace(e),asset_root='variant-root')
                self.assertTrue(r['strict_success'],r)
                self.assertEqual(r['spec_hash'],e['spec_hash'])
                self.assertEqual(r['evaluated_asset_manifest_sha256'],'c'*64)
                results.append(r)
            wrong=next(e for e in plan['episodes'] if e['target_id']=='SMA_2_2')
            with self.assertRaises(ValueError):w.resolve_workcell_episode(wrong,'variant-root')
            a['canonical_source_sha256']='e'*64
            chosen=next(e for e in plan['episodes'] if e['target_id']=='SMA_1_3')
            with self.assertRaisesRegex(ValueError,'source'):w.resolve_workcell_episode(chosen,'variant-root')
        report=w.aggregate_workcell_results(plan,results)['overall']
        self.assertEqual(report['planned'],29)
        self.assertEqual(report['completed'],3)
        self.assertEqual(report['success'],3)
        self.assertEqual(report['not_run'],26)
        bad=copy.deepcopy(results[0]);bad['evaluated_binding']['active']=False
        bad['result_sha256']=w._digest({k:v for k,v in bad.items() if k!='result_sha256'})
        with self.assertRaises(ValueError):w.aggregate_workcell_results(plan,[bad])

    def test_result_types_rejected_even_after_rehash(self):
        p=w.make_workcell_plan(['lid_open']);e=p['episodes'][0]
        r=w.score_workcell_trace(e,trace(e))
        for key,value in [('sample_count',True),('progress',{'done':True}),
                          ('failure_reasons','none'),('terminal_hold_s',31.)]:
            bad=dict(r);bad[key]=value
            bad['result_sha256']=w._digest({k:v for k,v in bad.items() if k!='result_sha256'})
            with self.assertRaises(ValueError):w.aggregate_workcell_results(p,[bad])

    def test_discontinuous_pose_not_a_successful_teleport(self):
        e=episode();data=trace(e);data[5]['goal_relative_position_m']=[0.,0.,0.]
        self.assertEqual(w.score_workcell_trace(e,data)['status'],'invalid')


if __name__=='__main__':unittest.main()
