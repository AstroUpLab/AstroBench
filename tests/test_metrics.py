"""Standard-library CPU tests; no simulator, torch, or GPU imports."""

import copy
import json
import math
import unittest

from astrobench.metrics import MetricsValidationError, aggregate_results, wilson95


def episode(task="cube", condition="G", pair="p0", seed=0, suite="grasp"):
    return {
        "episode_id": f"{suite}/{task}/{pair}/{condition}",
        "task_id": task,
        "suite": suite,
        "condition": condition,
        "pair_id": pair,
        "seed": seed,
        "spec_hash": f"hash-{suite}-{task}-{pair}-{condition}",
    }


def completed(plan, success=True, native=None):
    return {**plan, "status": "completed", "strict_success": success, "native_success": native}


def runtime_error(plan):
    return {**plan, "status": "runtime_error", "strict_success": None, "error": "simulator failed"}


class MetricsValidationTests(unittest.TestCase):
    def assert_invalid(self, plan, results, pattern=None, **kwargs):
        with self.assertRaisesRegex(MetricsValidationError, pattern or "."):
            aggregate_results(plan, results, **kwargs)

    def test_duplicate_results_are_not_extra_trials(self):
        p = episode()
        self.assert_invalid([p], [completed(p), completed(p)], "duplicate result")

    def test_duplicate_plan_ids_and_semantic_slots(self):
        p = episode()
        self.assert_invalid([p, p], [], "duplicate planned episode_id")
        self.assert_invalid([p, {**p, "episode_id": "other"}], [], "duplicate planned task/condition/pair")

    def test_unknown_result(self):
        self.assert_invalid([episode()], [completed(episode(task="unknown"))], "unknown result")

    def test_wrong_identity_labels_seeds_and_hashes(self):
        p = episode()
        for field, wrong in (("condition", "S"), ("task_id", "peg"), ("suite", "operation"),
                             ("pair_id", "p99"), ("seed", 99), ("spec_hash", "wrong")):
            with self.subTest(field=field):
                self.assert_invalid([p], [{**completed(p), field: wrong}], field)

    def test_missing_identity_fields(self):
        p = episode()
        for field in p:
            bad = completed(p)
            del bad[field]
            with self.subTest(field=field):
                self.assert_invalid([p], [bad], field)

    def test_paired_seed_mismatch_is_invalid_even_without_pair_request(self):
        self.assert_invalid([episode(condition="G", seed=0), episode(condition="S", seed=1)], [], "paired plan seeds")

    def test_pair_id_is_scoped_to_suite_and_task(self):
        plan = [episode(task="cube", seed=3), episode(task="peg", seed=4, suite="operation")]
        self.assertEqual(aggregate_results(plan, [])['overall']['planned'], 2)

    def test_seed_must_not_be_bool_float_negative_or_nonfinite(self):
        for seed in (True, False, 0.0, -1, float("nan"), float("inf")):
            with self.subTest(seed=seed):
                self.assert_invalid([episode(seed=seed)], [])

    def test_nan_in_unused_metadata_is_rejected(self):
        p = episode()
        for bad_number in (math.nan, math.inf, -math.inf):
            with self.subTest(number=bad_number):
                self.assert_invalid([{**p, "extra": {"nested": [bad_number]}}], [], "non-finite")
                self.assert_invalid([p], [{**completed(p), "timing": [bad_number]}], "non-finite")
        self.assert_invalid({"episodes": [p], "extra": math.nan}, [], "non-finite")

    def test_non_json_metadata_and_empty_labels_are_rejected(self):
        p = episode()
        self.assert_invalid([p], [{**completed(p), "extra": object()}], "unsupported JSON")
        self.assert_invalid([{**p, "extra": {1: "bad key"}}], [], "JSON keys")
        for label in ("", " G", "G ", None, 3):
            self.assert_invalid([{**p, "condition": label}], [])

    def test_completed_strict_success_must_be_explicit_bool(self):
        p = episode()
        for strict in (None, 1, 0, "true", [], math.nan):
            with self.subTest(strict=strict):
                self.assert_invalid([p], [completed(p, strict, native=True)])
        bad = completed(p)
        del bad["strict_success"]
        self.assert_invalid([p], [bad], "strict_success is required")

    def test_runtime_error_requires_explicit_null_strict_success(self):
        p = episode()
        for strict in (True, False, 0, "false"):
            self.assert_invalid([p], [{**runtime_error(p), "strict_success": strict}], "runtime_error strict_success")
        bad = runtime_error(p)
        del bad["strict_success"]
        self.assert_invalid([p], [bad], "strict_success is required")

    def test_native_success_and_status_validation(self):
        p = episode()
        for native in (1, 0, "yes", []):
            self.assert_invalid([p], [completed(p, native=native)], "native_success")
        for status in (None, "failed", "success", 1, ["completed"]):
            self.assert_invalid([p], [{**completed(p), "status": status}], "invalid status")

    def test_empty_or_invalid_plan_and_record_containers(self):
        for plan in ([], {}, "[]", None, ["episode"]):
            self.assert_invalid(plan, [])
        self.assert_invalid([episode()], {})
        self.assert_invalid([episode()], [None])

    def test_shared_extra_labels_must_match(self):
        p = {**episode(), "object_id": "cube-v1", "checkpoint_id": "abc", "optional_counter": 1}
        for field, value in (("object_id", "cube-v2"), ("checkpoint_id", "def"), ("optional_counter", True)):
            self.assert_invalid([p], [{**completed(p), field: value}], field)


class MetricsAggregationTests(unittest.TestCase):
    def test_all_success_complete_and_wilson_interval(self):
        plan = [episode(pair=f"p{i}", seed=i) for i in range(10)]
        report = aggregate_results(plan, [completed(p) for p in plan])
        counts = report["overall"]
        self.assertEqual((counts["planned"], counts["completed"], counts["success"], counts["fail"]), (10, 10, 10, 0))
        self.assertTrue(counts["complete"])
        self.assertTrue(counts["execution_complete"])
        self.assertEqual(counts["coverage_status"], "complete")
        self.assertAlmostEqual(counts["strict_success_wilson95"][0], 0.7224672, places=6)
        self.assertAlmostEqual(counts["strict_success_wilson95"][1], 1.0)
        self.assertEqual(report["macro_by_condition"][0]["full_macro_success_rate"], 1.0)
        self.assertIsNone(report["paired"])

    def test_empty_results_are_not_failures_or_zero_success_rate(self):
        report = aggregate_results([episode()], [])
        counts = report["overall"]
        self.assertEqual((counts["missing"], counts["fail"], counts["completed"]), (1, 0, 0))
        self.assertFalse(counts["complete"])
        self.assertEqual(counts["coverage_status"], "not_started")
        self.assertIsNone(counts["strict_success_rate"])
        self.assertIsNone(counts["strict_success_wilson95"])
        self.assertEqual(report["macro_by_condition"][0]["evaluable_tasks"], 0)

    def test_partial_results_keep_errors_and_missing_separate(self):
        plan = [episode(pair=f"p{i}", seed=i) for i in range(4)]
        report = aggregate_results(plan, [completed(plan[0], True), completed(plan[1], False), runtime_error(plan[2])])
        c = report["overall"]
        self.assertEqual((c["planned"], c["completed"], c["runtime_errors"], c["missing"], c["success"], c["fail"]), (4, 2, 1, 1, 1, 1))
        self.assertEqual(c["strict_success_rate"], 0.5)
        self.assertEqual(c["rate_denominator"], 2)
        self.assertEqual(c["strict_success_wilson95"], wilson95(1, 2))
        self.assertFalse(c["complete"])
        self.assertFalse(c["execution_complete"])
        self.assertEqual(c["missing_episode_ids"], [plan[3]["episode_id"]])
        self.assertEqual(c["runtime_error_episode_ids"], [plan[2]["episode_id"]])
        macro = report["macro_by_condition"][0]
        self.assertEqual(macro["observed_macro_success_rate"], 0.5)
        self.assertIsNone(macro["full_macro_success_rate"])

    def test_all_results_present_but_errors_is_not_complete(self):
        p = episode()
        c = aggregate_results([p], [runtime_error(p)])["overall"]
        self.assertTrue(c["execution_complete"])
        self.assertFalse(c["complete"])
        self.assertEqual(c["coverage_status"], "partial")
        self.assertEqual(c["fail"], 0)
        self.assertIsNone(c["strict_success_rate"])

    def test_native_success_never_substitutes_for_strict_success(self):
        plan = [episode(pair=f"p{i}", seed=i) for i in range(3)]
        results = [completed(plan[0], False, True), completed(plan[1], True, False), completed(plan[2], True)]
        c = aggregate_results(plan, results)["overall"]
        self.assertEqual((c["success"], c["fail"]), (2, 1))
        self.assertEqual((c["native"]["success"], c["native"]["fail"], c["native"]["unknown"]), (1, 1, 1))
        self.assertEqual(c["native"]["success_rate"], 0.5)

    def test_macro_weights_tasks_equally_and_keeps_suites_separate(self):
        many = [episode(task="cube", pair=f"p{i}", seed=i) for i in range(9)]
        rare = episode(task="bottle")
        operation = episode(task="drawer", suite="operation")
        plan = many + [rare, operation]
        report = aggregate_results(plan, [completed(p, True) for p in many] + [completed(rare, False), completed(operation, False)])
        self.assertAlmostEqual(report["overall"]["strict_success_rate"], 9 / 11)
        self.assertAlmostEqual(report["macro_by_condition"][0]["full_macro_success_rate"], 1 / 3)
        suites = {r["suite"]: r for r in report["macro_by_suite_condition"]}
        self.assertEqual(suites["grasp"]["full_macro_success_rate"], 0.5)
        self.assertEqual(suites["operation"]["full_macro_success_rate"], 0.0)

    def test_missing_entire_task_is_visible_in_macro(self):
        a, b = episode(task="a"), episode(task="b")
        macro = aggregate_results([a, b], [completed(a)])["macro_by_condition"][0]
        self.assertEqual((macro["planned_tasks"], macro["evaluable_tasks"], macro["complete_tasks"]), (2, 1, 1))
        self.assertEqual(macro["observed_macro_success_rate"], 1)
        self.assertEqual(macro["task_coverage_fraction"], 0.5)
        self.assertIsNone(macro["full_macro_success_rate"])

    def test_plan_envelope_inputs_unchanged_and_output_json_finite(self):
        p = episode()
        plan = {"episodes": [p], "schema_version": 1}
        results = [completed(p)]
        before = copy.deepcopy((plan, results))
        report = aggregate_results(plan, results)
        self.assertEqual((plan, results), before)
        json.dumps(report, allow_nan=False)

    def test_order_does_not_change_report(self):
        plan = [episode(task="b", condition="S"), episode(task="a"), episode(task="b")]
        results = [completed(p, i % 2 == 0) for i, p in enumerate(plan)]
        self.assertEqual(aggregate_results(plan, results, paired_conditions=("G", "S")),
                         aggregate_results(plan[::-1], results[::-1], paired_conditions=("G", "S")))


class PairedTests(unittest.TestCase):
    def test_pairing_uses_matched_completed_pairs_only(self):
        plan = [episode(condition=c, pair=f"p{i}", seed=i) for i in range(3) for c in ("G", "S")]
        results = [completed(plan[0], False), completed(plan[1], True),
                   completed(plan[2], True), runtime_error(plan[3]), completed(plan[4], False)]
        report = aggregate_results(plan, results, paired_conditions=("G", "S"))
        paired = report["paired"]["overall"]
        self.assertEqual((paired["planned_pairs"], paired["completed_pairs"], paired["runtime_error_pairs"], paired["missing_pairs"]), (3, 1, 1, 1))
        self.assertEqual(paired["mean_difference_b_minus_a"], 1.0)
        self.assertEqual(paired["outcomes"]["a0_b1"], 1)
        self.assertFalse(paired["complete"])
        self.assertIsNone(report["paired"]["macro"]["full_macro_difference_b_minus_a"])
        self.assertEqual(report["paired"]["macro"]["observed_macro_difference_b_minus_a"], 1)

    def test_paired_difference_sign_and_all_four_outcomes(self):
        plan = [episode(condition=c, pair=f"p{i}", seed=i) for i in range(4) for c in ("G", "S")]
        outcomes = [(False, False), (False, True), (True, False), (True, True)]
        results = [completed(plan[2*i+j], outcome[j]) for i, outcome in enumerate(outcomes) for j in range(2)]
        r = aggregate_results(plan, results, paired_conditions=("G", "S"))["paired"]
        self.assertEqual(r["overall"]["outcomes"], {"a0_b0": 1, "a0_b1": 1, "a1_b0": 1, "a1_b1": 1})
        self.assertEqual(r["overall"]["mean_difference_b_minus_a"], 0)
        self.assertTrue(r["overall"]["complete"])
        reverse = aggregate_results(plan[:2], [completed(plan[0], False), completed(plan[1], True)], paired_conditions=("S", "G"))
        self.assertEqual(reverse["paired"]["overall"]["mean_difference_b_minus_a"], -1)

    def test_unpaired_plan_is_visible_not_silently_dropped(self):
        plan = [episode(condition="G"), episode(condition="S"), episode(pair="p1", seed=1)]
        paired = aggregate_results(plan, [completed(p) for p in plan], paired_conditions=("G", "S"))["paired"]
        c = paired["overall"]
        self.assertEqual((c["planned_pair_candidates"], c["planned_pairs"], c["completed_pairs"], c["unpaired_plan_pairs"]), (2, 1, 1, 1))
        self.assertFalse(c["complete"])
        self.assertIsNone(paired["macro"]["full_macro_difference_b_minus_a"])

    def test_pair_status_prioritizes_error_over_missing_without_double_counting(self):
        plan = [episode(condition=c) for c in ("G", "S")]
        c = aggregate_results(plan, [runtime_error(plan[0])], paired_conditions=("G", "S"))["paired"]["overall"]
        self.assertEqual((c["runtime_error_pairs"], c["missing_pairs"], c["incomplete_pairs"]), (1, 0, 1))
        self.assertIsNone(c["mean_difference_b_minus_a"])

    def test_paired_macro_is_task_equal_not_pair_equal(self):
        plan = [episode(task="many", condition=c, pair=f"p{i}", seed=i) for i in range(9) for c in ("G", "S")]
        plan += [episode(task="rare", condition=c) for c in ("G", "S")]
        results = [completed(p, p["condition"] == "S" if p["task_id"] == "many" else p["condition"] == "G") for p in plan]
        paired = aggregate_results(plan, results, paired_conditions=("G", "S"))["paired"]
        self.assertEqual(paired["overall"]["mean_difference_b_minus_a"], 0.8)
        self.assertEqual(paired["macro"]["full_macro_difference_b_minus_a"], 0.0)

    def test_pairs_do_not_cross_task_or_suite(self):
        plan = [episode(task="same", suite=s, condition=c, seed=i) for i, s in enumerate(("grasp", "operation")) for c in ("G", "S")]
        results = [completed(plan[0]), completed(plan[3])]
        paired = aggregate_results(plan, results, paired_conditions=("G", "S"))["paired"]
        self.assertEqual(paired["overall"]["completed_pairs"], 0)
        self.assertEqual(paired["overall"]["missing_pairs"], 2)
        self.assertEqual(len(paired["by_task"]), 2)
        self.assertIsNone(paired["macro"]["observed_macro_difference_b_minus_a"])

    def test_other_conditions_do_not_pollute_selected_pairs(self):
        plan = [episode(condition=c) for c in ("G", "V", "P", "S")]
        report = aggregate_results(plan, [completed(plan[0]), completed(plan[3])], paired_conditions=("G", "S"))
        self.assertTrue(report["paired"]["overall"]["complete"])
        self.assertFalse(report["overall"]["complete"])

    def test_bad_pair_specs_are_rejected(self):
        plan = [episode(condition=c) for c in ("G", "S")]
        for conditions in ("GS", ("G",), ("G", "G"), ("G", "unknown"), ("G", "S", "V"), ("G", None)):
            with self.subTest(conditions=conditions), self.assertRaises(MetricsValidationError):
                aggregate_results(plan, [], paired_conditions=conditions)


class WilsonTests(unittest.TestCase):
    def test_reference_values_and_empty_interval(self):
        self.assertIsNone(wilson95(0, 0))
        self.assertAlmostEqual(wilson95(0, 10)[1], 0.2775328, places=6)
        lower, upper = wilson95(5, 10)
        self.assertAlmostEqual(lower, 0.2365931, places=6)
        self.assertAlmostEqual(upper, 0.7634069, places=6)

    def test_reject_noninteger_or_invalid_counts(self):
        for s, n in ((True, 2), (1.0, 2), (0, False), (-1, 2), (3, 2), (0, -1), (math.nan, 2)):
            with self.subTest(successes=s, total=n), self.assertRaises(MetricsValidationError):
                wilson95(s, n)


if __name__ == "__main__":
    unittest.main()
