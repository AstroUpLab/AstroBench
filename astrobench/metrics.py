"""Strict, CPU-only aggregation of preregistered SpaceBench episodes.

``aggregate_results(plan_episodes, result_episodes, paired_conditions=("G", "S"))``
accepts JSON records, not files. A plan envelope with an ``episodes`` list is also
accepted. Every plan/result record must have the seven IDENTITY_FIELDS below.
Results additionally require ``status`` and ``strict_success``: completed
episodes require an actual bool; runtime errors require explicit None. Optional
``native_success`` is reported separately and never substitutes for strict
success. IDs, labels, seeds, and episode spec hashes must match exactly.

Success rates and Wilson intervals use completed episodes only. ``complete``
means *every planned episode completed*, whereas ``execution_complete`` means
every planned episode has a result (possibly a runtime error). Observed rates
are consequently provisional whenever ``complete`` is false. Macro rates give
each (suite, task_id) equal weight; full macro rates are withheld until complete.
Paired differences are B minus A on complete strict-success pairs only, never
the difference between two independently filtered marginal success rates.

This module intentionally does not verify spec-hash cryptographic provenance:
the plan author/loader must do that before calling it. Non-finite or non-JSON
values anywhere in input are rejected, including otherwise-unused metadata.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
import math
import hashlib
import json
from statistics import NormalDist
from typing import Any


IDENTITY_FIELDS = (
    "episode_id", "task_id", "suite", "condition", "pair_id", "seed", "spec_hash",
)
_TEXT_FIELDS = tuple(field for field in IDENTITY_FIELDS if field != "seed")
_Z95 = NormalDist().inv_cdf(0.975)


class MetricsValidationError(ValueError):
    """An input cannot truthfully be aggregated against the registered plan."""


def _json_values(value: Any, path: str) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise MetricsValidationError(f"{path}: non-finite numeric value")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise MetricsValidationError(f"{path}: JSON keys must be strings")
            _json_values(item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _json_values(item, f"{path}[{index}]")
        return
    raise MetricsValidationError(f"{path}: unsupported JSON value {type(value).__name__}")


def _records(value: Any, name: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise MetricsValidationError(f"{name} must be a sequence of episode records")
    records = list(value)
    _json_values(records, name)
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise MetricsValidationError(f"{name}[{index}] must be a mapping")
        for field in _TEXT_FIELDS:
            text = record.get(field)
            if type(text) is not str or not text.strip() or text != text.strip():
                raise MetricsValidationError(f"{name}[{index}].{field} must be a nonempty label without edge whitespace")
        seed = record.get("seed")
        if type(seed) is not int or seed < 0:
            raise MetricsValidationError(f"{name}[{index}].seed must be a nonnegative integer, not bool/float")
    return records


def _protocol_json(protocol: Any) -> str:
    if not isinstance(protocol, Mapping) or not protocol:
        raise MetricsValidationError("protocol must be a nonempty JSON object")
    try:
        return json.dumps(protocol, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MetricsValidationError("protocol must be a finite JSON object") from exc


def _protocol_signature(episodes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Do not pool revisions, even when task/seed/condition slots are disjoint.

    Historical generic callers may omit protocol on *every* planned episode.
    A partly declared protocol cannot establish a common scoring population.
    """
    declared = ["protocol" in episode for episode in episodes]
    if not any(declared):
        return {"declared": False, "version": None, "sha256": None}
    if not all(declared):
        raise MetricsValidationError("mixed declared/missing protocol in plan; aggregate each protocol separately")
    canonical = [_protocol_json(episode["protocol"]) for episode in episodes]
    if len(set(canonical)) != 1:
        raise MetricsValidationError("mixed protocol definitions in plan; aggregate each complete protocol separately")
    return {"declared": True, "version": episodes[0]["protocol"].get("version"),
            "sha256": hashlib.sha256(canonical[0].encode()).hexdigest()}


def wilson95(successes: int, total: int) -> list[float] | None:
    """Two-sided 95% Wilson binomial interval; None for an empty denominator."""
    if type(successes) is not int or type(total) is not int or not 0 <= successes <= total:
        raise MetricsValidationError("Wilson counts must be integers with 0 <= successes <= total")
    if total == 0:
        return None
    z2 = _Z95 * _Z95
    rate = successes / total
    denominator = 1 + z2 / total
    center = (rate + z2 / (2 * total)) / denominator
    half_width = _Z95 * math.sqrt(rate * (1 - rate) / total + z2 / (4 * total * total)) / denominator
    return [max(0.0, center - half_width), min(1.0, center + half_width)]


def _completion(planned: int, completed: int, present: int) -> dict[str, Any]:
    complete = planned > 0 and completed == planned
    return {
        "complete": complete,
        "execution_complete": planned > 0 and present == planned,
        "coverage_status": "complete" if complete else ("not_started" if present == 0 else "partial"),
        "completion_fraction": completed / planned if planned else None,
    }


def _counts(episodes: Sequence[Mapping[str, Any]], results: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    completed = errors = success = native_success = native_fail = 0
    missing_ids: list[str] = []
    error_ids: list[str] = []
    for episode in episodes:
        episode_id = episode["episode_id"]
        result = results.get(episode_id)
        if result is None:
            missing_ids.append(episode_id)
        elif result["status"] == "runtime_error":
            errors += 1
            error_ids.append(episode_id)
        else:
            completed += 1
            success += int(result["strict_success"])
            if result.get("native_success") is True:
                native_success += 1
            elif result.get("native_success") is False:
                native_fail += 1
    planned = len(episodes)
    native_known = native_success + native_fail
    return {
        "planned": planned,
        "completed": completed,
        "runtime_errors": errors,
        "missing": len(missing_ids),
        "success": success,
        "fail": completed - success,
        "strict_success_rate": success / completed if completed else None,
        "strict_success_wilson95": wilson95(success, completed),
        "rate_denominator": completed,
        "rate_population": "completed_only",
        "native": {
            "success": native_success,
            "fail": native_fail,
            "unknown": completed - native_known,
            "rate_denominator": native_known,
            "success_rate": native_success / native_known if native_known else None,
            "success_wilson95": wilson95(native_success, native_known),
        },
        "missing_episode_ids": sorted(missing_ids),
        "runtime_error_episode_ids": sorted(error_ids),
        **_completion(planned, completed, completed + errors),
    }


def _group_counts(episodes, results, fields):
    groups = defaultdict(list)
    for episode in episodes:
        groups[tuple(episode[field] for field in fields)].append(episode)
    return [
        {**dict(zip(fields, key)), **_counts(group, results)}
        for key, group in sorted(groups.items())
    ]


def _macro(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observed = [row["strict_success_rate"] for row in rows if row["completed"] > 0]
    planned = sum(row["planned"] for row in rows)
    completed = sum(row["completed"] for row in rows)
    errors = sum(row["runtime_errors"] for row in rows)
    complete = bool(rows) and all(row["complete"] for row in rows)
    rate = sum(observed) / len(observed) if observed else None
    return {
        "planned_tasks": len(rows),
        "evaluable_tasks": len(observed),
        "complete_tasks": sum(row["complete"] for row in rows),
        "planned": planned,
        "completed": completed,
        "runtime_errors": errors,
        "missing": sum(row["missing"] for row in rows),
        "task_coverage_fraction": len(observed) / len(rows) if rows else None,
        "observed_macro_success_rate": rate,
        "full_macro_success_rate": rate if complete else None,
        "weighting": "equal_per_suite_task_id_not_per_episode",
        "rate_population": "tasks_with_at_least_one_completed_episode",
        **_completion(planned, completed, completed + errors),
    }


def _macro_groups(task_rows, fields):
    groups = defaultdict(list)
    for row in task_rows:
        groups[tuple(row[field] for field in fields)].append(row)
    return [{**dict(zip(fields, key)), **_macro(rows)} for key, rows in sorted(groups.items())]


def _pair_counts(pair_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    valid = [pair for pair in pair_records if pair["status"] == "completed"]
    planned = sum(pair["status"] != "unpaired_plan" for pair in pair_records)
    unpaired = len(pair_records) - planned
    errors = sum(pair["status"] == "runtime_error" for pair in pair_records)
    missing = sum(pair["status"] == "missing" for pair in pair_records)
    n = len(valid)
    outcomes = {
        f"a{a}_b{b}": sum(pair["success_a"] == bool(a) and pair["success_b"] == bool(b) for pair in valid)
        for a in (0, 1) for b in (0, 1)
    }
    complete = bool(pair_records) and n == len(pair_records)
    present = sum(pair["both_results_present"] for pair in pair_records)
    return {
        "planned_pair_candidates": len(pair_records),
        "planned_pairs": planned,
        "completed_pairs": n,
        "runtime_error_pairs": errors,
        "missing_pairs": missing,
        "unpaired_plan_pairs": unpaired,
        "incomplete_pairs": len(pair_records) - n,
        "success_rate_a": sum(pair["success_a"] for pair in valid) / n if n else None,
        "success_rate_b": sum(pair["success_b"] for pair in valid) / n if n else None,
        "mean_difference_b_minus_a": sum(pair["difference_b_minus_a"] for pair in valid) / n if n else None,
        "outcomes": outcomes,
        "complete": complete,
        "execution_complete": bool(pair_records) and present == len(pair_records),
        "coverage_status": "complete" if complete else ("not_started" if not any(pair["any_result_present"] for pair in pair_records) else "partial"),
        "completion_fraction": n / len(pair_records) if pair_records else None,
        "rate_population": "both_conditions_completed_only",
    }


def _paired(episodes, results, conditions):
    condition_a, condition_b = conditions
    groups = defaultdict(dict)
    for episode in episodes:
        if episode["condition"] in conditions:
            groups[(episode["suite"], episode["task_id"], episode["pair_id"])][episode["condition"]] = episode
    pairs = []
    for (suite, task_id, pair_id), group in sorted(groups.items()):
        a, b = group.get(condition_a), group.get(condition_b)
        ra = results.get(a["episode_id"]) if a else None
        rb = results.get(b["episode_id"]) if b else None
        if a is None or b is None:
            status = "unpaired_plan"
        elif any(result is not None and result["status"] == "runtime_error" for result in (ra, rb)):
            status = "runtime_error"
        elif ra is None or rb is None:
            status = "missing"
        else:
            status = "completed"
        valid = status == "completed"
        pairs.append({
            "suite": suite, "task_id": task_id, "pair_id": pair_id,
            "seed": (a if a is not None else b)["seed"],
            "episode_id_a": a["episode_id"] if a else None,
            "episode_id_b": b["episode_id"] if b else None,
            "status": status,
            "both_results_present": ra is not None and rb is not None,
            "any_result_present": ra is not None or rb is not None,
            "success_a": ra["strict_success"] if valid else None,
            "success_b": rb["strict_success"] if valid else None,
            "difference_b_minus_a": int(rb["strict_success"]) - int(ra["strict_success"]) if valid else None,
        })
    task_groups = defaultdict(list)
    suite_groups = defaultdict(list)
    for pair in pairs:
        task_groups[(pair["suite"], pair["task_id"])].append(pair)
        suite_groups[pair["suite"]].append(pair)
    task_rows = [
        {"suite": suite, "task_id": task, **_pair_counts(group)}
        for (suite, task), group in sorted(task_groups.items())
    ]

    def paired_macro(rows):
        rates = [row["mean_difference_b_minus_a"] for row in rows if row["completed_pairs"] > 0]
        complete = bool(rows) and all(row["complete"] for row in rows)
        observed = sum(rates) / len(rates) if rates else None
        return {
            "planned_tasks": len(rows), "evaluable_tasks": len(rates),
            "complete_tasks": sum(row["complete"] for row in rows),
            "observed_macro_difference_b_minus_a": observed,
            "full_macro_difference_b_minus_a": observed if complete else None,
            "complete": complete,
            "weighting": "equal_per_suite_task_id_not_per_pair",
            "rate_population": "tasks_with_at_least_one_completed_pair",
        }

    return {
        "condition_a": condition_a, "condition_b": condition_b,
        "difference_definition": "condition_b_strict_success_minus_condition_a_strict_success",
        "incomplete_status_priority": "unpaired_plan_then_runtime_error_then_missing",
        "overall": _pair_counts(pairs),
        "by_task": task_rows,
        "by_suite": [{"suite": suite, **_pair_counts(group)} for suite, group in sorted(suite_groups.items())],
        "macro": paired_macro(task_rows),
        "macro_by_suite": [
            {"suite": suite, **paired_macro([row for row in task_rows if row["suite"] == suite])}
            for suite in sorted(suite_groups)
        ],
        "pairs": pairs,
    }


def aggregate_results(
    planned_episodes: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    episode_results: Sequence[Mapping[str, Any]],
    *,
    paired_conditions: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Validate all input before producing any statistics; never mutate input.

    Additional shared plan/result fields must also match (e.g. object_id or
    checkpoint_id), but only IDENTITY_FIELDS are mandatory in results. Identity
    comparison is type-strict, so neither True==1 nor 1.0==1 passes. Different
    conditions in a registered (suite, task_id, pair_id) must share a seed.
    """
    if isinstance(planned_episodes, Mapping):
        _json_values(planned_episodes, "plan")
        if "episodes" not in planned_episodes:
            raise MetricsValidationError("plan envelope must contain episodes")
        planned_episodes = planned_episodes["episodes"]
    episodes = _records(planned_episodes, "plan.episodes")
    if not episodes:
        raise MetricsValidationError("plan must contain at least one episode")
    protocol_signature = _protocol_signature(episodes)
    incoming = _records(episode_results, "results")
    plan_by_id = {}
    slots = set()
    pair_seeds = {}
    for episode in episodes:
        episode_id = episode["episode_id"]
        if episode_id in plan_by_id:
            raise MetricsValidationError(f"duplicate planned episode_id: {episode_id}")
        slot = (episode["suite"], episode["task_id"], episode["condition"], episode["pair_id"])
        if slot in slots:
            raise MetricsValidationError(f"duplicate planned task/condition/pair slot: {slot}")
        pair = (episode["suite"], episode["task_id"], episode["pair_id"])
        if pair in pair_seeds and pair_seeds[pair] != episode["seed"]:
            raise MetricsValidationError(f"paired plan seeds differ: {pair}")
        plan_by_id[episode_id] = episode
        slots.add(slot)
        pair_seeds[pair] = episode["seed"]
    results = {}
    for result in incoming:
        episode_id = result["episode_id"]
        if episode_id in results:
            raise MetricsValidationError(f"duplicate result episode_id: {episode_id}")
        if episode_id not in plan_by_id:
            raise MetricsValidationError(f"unknown result episode_id: {episode_id}")
        planned = plan_by_id[episode_id]
        if "protocol" in result:
            if "protocol" not in planned or _protocol_json(result["protocol"]) != _protocol_json(planned["protocol"]):
                raise MetricsValidationError(f"result {episode_id}: protocol does not match plan")
        for field in planned.keys() & result.keys():
            if type(planned[field]) is not type(result[field]) or planned[field] != result[field]:
                raise MetricsValidationError(f"result {episode_id}: {field} does not match plan")
        status = result.get("status")
        if status not in ("completed", "runtime_error"):
            raise MetricsValidationError(f"result {episode_id}: invalid status")
        if "strict_success" not in result:
            raise MetricsValidationError(f"result {episode_id}: strict_success is required")
        strict = result["strict_success"]
        if status == "completed" and type(strict) is not bool:
            raise MetricsValidationError(f"result {episode_id}: completed strict_success must be an explicit bool")
        if status == "runtime_error" and strict is not None:
            raise MetricsValidationError(f"result {episode_id}: runtime_error strict_success must be null")
        if result.get("native_success") is not None and type(result["native_success"]) is not bool:
            raise MetricsValidationError(f"result {episode_id}: native_success must be bool or null")
        results[episode_id] = result
    if paired_conditions is not None:
        if not isinstance(paired_conditions, (list, tuple)) or len(paired_conditions) != 2:
            raise MetricsValidationError("paired_conditions must be a two-element list/tuple")
        available = {episode["condition"] for episode in episodes}
        if any(type(condition) is not str or condition not in available for condition in paired_conditions):
            raise MetricsValidationError("paired_conditions must name registered conditions")
        if paired_conditions[0] == paired_conditions[1]:
            raise MetricsValidationError("paired_conditions must be distinct")
    task_rows = _group_counts(episodes, results, ("suite", "task_id", "condition"))
    return {
        "schema_version": 1,
        "protocol": protocol_signature,
        "overall": _counts(episodes, results),
        "by_task_condition": task_rows,
        "by_suite_condition": _group_counts(episodes, results, ("suite", "condition")),
        "by_condition": _group_counts(episodes, results, ("condition",)),
        "macro_by_condition": _macro_groups(task_rows, ("condition",)),
        "macro_by_suite_condition": _macro_groups(task_rows, ("suite", "condition")),
        "paired": _paired(episodes, results, paired_conditions) if paired_conditions is not None else None,
        "notes": [
            "Missing and runtime-error episodes are not successes or task failures.",
            "Observed success rates/intervals condition on valid completed episodes, not the full plan.",
            "Native success is diagnostic only; it never fills missing strict_success.",
            "Wilson95 intervals are binomial episode intervals, not macro or paired-difference intervals.",
        ],
    }
