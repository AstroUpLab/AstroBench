import copy
import unittest
from astrobench.protocol import make_plan, validate_plan, score_trace


def catalog():
    return [dict(object_id='example', asset_sha256='a'*64, split='test', geometry_group='example')]


def trace():
    return [dict(t_s=i/50, left_target_force_n=1.0, right_target_force_n=1.0,
        closed=True, forbidden_contact=False, escaped=False,
        relative_linear_speed_m_s=0., relative_angular_speed_rad_s=0.,
        relative_position_m=[0.,0.,0.], relative_quat_wxyz=[1.,0.,0.,0.]) for i in range(601)]


class ProtocolTests(unittest.TestCase):
    def test_determinism_and_validation(self):
        p = make_plan(catalog(), 4)
        self.assertEqual(p, make_plan(catalog(), 4))
        self.assertEqual(len(p['episodes']), 4)
        self.assertEqual(validate_plan(p), p)

    def test_leakage_by_group_and_bytes(self):
        for field in ('geometry_group','asset_sha256'):
            rows = catalog()
            other = dict(object_id='other', asset_sha256='b'*64, split='train', geometry_group='other')
            other[field] = rows[0][field]
            with self.assertRaises(ValueError): make_plan(rows+[other])

    def test_tampering_and_dropping_episodes(self):
        for mutation in ('hash','label','drop'):
            p = make_plan(catalog())
            if mutation=='hash': p['episodes'][0]['spec']['track']='wrong'
            elif mutation=='label': p['episodes'][0]['suite']='train/static'
            else: p['episodes'].pop()
            with self.assertRaises(ValueError): validate_plan(p)

    def test_seed_types(self):
        for seed in (True,-1,1.0,2**64):
            with self.assertRaises(ValueError): make_plan(catalog(),seed)

    def test_terminal_retention(self):
        self.assertTrue(score_trace(trace())['strict_success'])
        data = trace()
        for s in data[-20:]: s['right_target_force_n']=0.
        result = score_trace(data)
        self.assertFalse(result['strict_success'])
        self.assertEqual(result['certified_grasp_losses'],1)
        self.assertEqual(result['time_to_stable_capture_s'],1.)

    def test_reacquisition_after_loss(self):
        data = trace(); data[200]['closed']=False
        result = score_trace(data)
        self.assertTrue(result['strict_success'])
        self.assertEqual(result['certified_grasp_losses'],1)

    def test_forbidden_contact_escape_and_speed(self):
        for key,value in [('forbidden_contact',True),('escaped',True),
                ('relative_linear_speed_m_s',.1),('relative_angular_speed_rad_s',1.)]:
            data = trace(); data[-1][key]=value
            self.assertFalse(score_trace(data)['strict_success'])

    def test_pose_drift_and_quaternion_sign(self):
        data = trace()
        for s in data: s['relative_quat_wxyz']=[-1.,0.,0.,0.]
        self.assertTrue(score_trace(data)['strict_success'])
        data[-1]['relative_position_m']=[.02,0.,0.]
        self.assertFalse(score_trace(data)['strict_success'])

    def test_exact_window_boundary(self):
        data=trace()
        for s in data[:550]: s['closed']=False
        self.assertTrue(score_trace(data)['strict_success'])
        data[550]['closed']=False
        self.assertFalse(score_trace(data)['strict_success'])

    def test_bad_trace_is_error_not_failure(self):
        data=trace()
        bads=[data[:-1],data[1:],data[:200]+data[202:]]
        for key,value in [('closed',1),('t_s',float('nan')),
                          ('relative_quat_wxyz',[0,0,0,0]),('left_target_force_n',-1)]:
            bad=copy.deepcopy(data); bad[300][key]=value; bads.append(bad)
        for bad in bads:
            with self.assertRaises(ValueError): score_trace(bad)


if __name__ == '__main__': unittest.main()
