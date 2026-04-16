from __future__ import annotations

import random
from collections import defaultdict
from typing import Any

DEFAULT_CHAIN_SYMBOLS = ("ろ", "ま", "か", "め", "せ")
DEFAULT_LEFT_KEY = "z"
DEFAULT_RIGHT_KEY = "m"
DEFAULT_CONTINUE_KEY = "space"
DEFAULT_RESPONSE_WINDOW_S = 3.0
DEFAULT_FEEDBACK_DURATION_S = 0.8
DEFAULT_ITI_DURATION_S = 0.4
DEFAULT_BLOCK_REPEAT_LIMIT = 3
DEFAULT_TRAINING_THRESHOLD = 0.8

TRAINING_CONDITION_ID = "training_premise"
TEST_PREMISE_CONDITION_ID = "test_premise"
TEST_TRANSITIVE_CONDITION_ID = "test_transitive"
TEST_ANCHOR_CONDITION_ID = "test_anchor"


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _trial_rng(seed: int, block_idx: int, trial_idx: int, attempt_idx: int = 0, salt: int = 0) -> random.Random:
    mixed = (
        (int(seed) + 1) * 1_000_003
        + (int(block_idx) + 1) * 10_009
        + (int(trial_idx) + 1) * 1_009
        + (int(attempt_idx) + 1) * 97
        + int(salt) * 31
    )
    return random.Random(mixed % (2**32))


def _to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if value is None:
        return {}
    try:
        return dict(value)
    except Exception:
        return {}


def _to_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def _normalize_pair_spec(spec: Any) -> dict[str, Any]:
    data = dict(spec or {})
    pair_id = str(data.get("pair_id", "")).strip().upper()
    correct_symbol = str(data.get("correct_symbol", "")).strip()
    foil_symbol = str(data.get("foil_symbol", "")).strip()

    if not pair_id:
        raise ValueError("pair specification is missing pair_id")
    if not correct_symbol or not foil_symbol:
        raise ValueError(f"pair specification {pair_id!r} is missing symbol assignments")

    return {
        "pair_id": pair_id,
        "correct_symbol": correct_symbol,
        "foil_symbol": foil_symbol,
    }


def _build_pair_map(settings: Any) -> dict[str, dict[str, Any]]:
    pair_map: dict[str, dict[str, Any]] = {}

    premise_pairs = _to_list(getattr(settings, "premise_pairs", None))
    for spec in premise_pairs:
        normalized = _normalize_pair_spec(spec)
        pair_map[normalized["pair_id"]] = {**normalized, "pair_kind": "premise"}

    probe_pairs = _to_dict(getattr(settings, "probe_pairs", None))
    for probe_name in ("transitive", "anchor"):
        if probe_name not in probe_pairs:
            continue
        normalized = _normalize_pair_spec(probe_pairs[probe_name])
        pair_map[normalized["pair_id"]] = {
            **normalized,
            "pair_kind": "probe",
            "probe_name": probe_name,
        }

    if not pair_map:
        chain = list(getattr(settings, "chain_symbols", DEFAULT_CHAIN_SYMBOLS))
        if len(chain) < 5:
            chain = list(DEFAULT_CHAIN_SYMBOLS)
        pair_map = {
            "AB": {"pair_id": "AB", "correct_symbol": chain[0], "foil_symbol": chain[1], "pair_kind": "premise"},
            "BC": {"pair_id": "BC", "correct_symbol": chain[1], "foil_symbol": chain[2], "pair_kind": "premise"},
            "CD": {"pair_id": "CD", "correct_symbol": chain[2], "foil_symbol": chain[3], "pair_kind": "premise"},
            "DE": {"pair_id": "DE", "correct_symbol": chain[3], "foil_symbol": chain[4], "pair_kind": "premise"},
            "BD": {"pair_id": "BD", "correct_symbol": chain[1], "foil_symbol": chain[3], "pair_kind": "probe", "probe_name": "transitive"},
            "AE": {"pair_id": "AE", "correct_symbol": chain[0], "foil_symbol": chain[4], "pair_kind": "probe", "probe_name": "anchor"},
        }

    return pair_map


def _expand_pattern(pattern: dict[str, Any], *, rng: random.Random | None = None) -> list[str]:
    pattern = _to_dict(pattern)
    cycle_count = max(1, _coerce_int(pattern.get("cycle_count", 1), 1))
    randomize = bool(pattern.get("randomize", False))
    pair_repeats = _to_list(pattern.get("pair_repeats", []))

    sequence: list[str] = []
    for _ in range(cycle_count):
        for item in pair_repeats:
            data = _to_dict(item)
            pair_id = str(data.get("pair_id", "")).strip().upper()
            repeat = max(1, _coerce_int(data.get("repeat", 1), 1))
            if not pair_id:
                continue
            sequence.extend([pair_id] * repeat)

    if randomize and sequence:
        (rng or random.Random(0)).shuffle(sequence)

    return sequence


def _trial_spec(
    *,
    block_kind: str,
    block_idx: int,
    block_label: str,
    trial_index_in_block: int,
    pair_id: str,
    pair_info: dict[str, Any],
    phase: str,
    condition_id: str,
    seed: int,
    block_attempt: int = 1,
) -> dict[str, Any]:
    return {
        "block_kind": block_kind,
        "block_idx": int(block_idx),
        "block_label": block_label,
        "block_attempt": int(block_attempt),
        "trial_phase": phase,
        "trial_index_in_block": int(trial_index_in_block),
        "pair_id": str(pair_id).upper(),
        "pair_kind": str(pair_info.get("pair_kind", "premise")),
        "condition_id": condition_id,
        "correct_symbol": str(pair_info["correct_symbol"]),
        "foil_symbol": str(pair_info["foil_symbol"]),
        "stimulus_summary": f'{pair_id}:{pair_info["correct_symbol"]}/{pair_info["foil_symbol"]}',
        "seed": int(seed),
    }


def build_session_plan(settings: Any) -> list[dict[str, Any]]:
    """Build the full human session schedule from config-defined pair patterns."""

    overall_seed = _coerce_int(getattr(settings, "overall_seed", 52052), 52052)
    pair_map = _build_pair_map(settings)
    training_patterns = _to_dict(getattr(settings, "training_block_patterns", None))
    test_pattern = _to_dict(getattr(settings, "test_block_pattern", None))

    if not training_patterns:
        training_patterns = {
            "block_1": {
                "cycle_count": 2,
                "randomize": False,
                "pair_repeats": [
                    {"pair_id": "AB", "repeat": 5},
                    {"pair_id": "BC", "repeat": 5},
                    {"pair_id": "CD", "repeat": 5},
                    {"pair_id": "DE", "repeat": 5},
                ],
            },
            "block_2": {
                "cycle_count": 5,
                "randomize": False,
                "pair_repeats": [
                    {"pair_id": "AB", "repeat": 2},
                    {"pair_id": "BC", "repeat": 2},
                    {"pair_id": "CD", "repeat": 2},
                    {"pair_id": "DE", "repeat": 2},
                ],
            },
            "block_3": {
                "cycle_count": 10,
                "randomize": False,
                "pair_repeats": [
                    {"pair_id": "AB", "repeat": 1},
                    {"pair_id": "BC", "repeat": 1},
                    {"pair_id": "CD", "repeat": 1},
                    {"pair_id": "DE", "repeat": 1},
                ],
            },
            "block_4": {
                "cycle_count": 1,
                "randomize": True,
                "pair_repeats": [
                    {"pair_id": "AB", "repeat": 10},
                    {"pair_id": "BC", "repeat": 10},
                    {"pair_id": "CD", "repeat": 10},
                    {"pair_id": "DE", "repeat": 10},
                ],
            },
        }

    if not test_pattern:
        test_pattern = {
            "cycle_count": 1,
            "randomize": True,
            "pair_repeats": [
                {"pair_id": "AB", "repeat": 8},
                {"pair_id": "BC", "repeat": 8},
                {"pair_id": "CD", "repeat": 8},
                {"pair_id": "DE", "repeat": 8},
                {"pair_id": "BD", "repeat": 8},
                {"pair_id": "AE", "repeat": 8},
            ],
        }

    blocks: list[dict[str, Any]] = []
    training_keys = ("block_1", "block_2", "block_3", "block_4")

    for block_idx, block_key in enumerate(training_keys):
        pattern = _to_dict(training_patterns.get(block_key))
        rng = _trial_rng(overall_seed, block_idx, 0, salt=17)
        sequence = _expand_pattern(pattern, rng=rng)
        trials: list[dict[str, Any]] = []
        for trial_index, pair_id in enumerate(sequence, start=1):
            pair_info = pair_map[pair_id]
            trials.append(
                _trial_spec(
                    block_kind="training",
                    block_idx=block_idx,
                    block_label=f"Training Block {block_idx + 1}",
                    trial_index_in_block=trial_index,
                    pair_id=pair_id,
                    pair_info=pair_info,
                    phase="training",
                    condition_id=TRAINING_CONDITION_ID,
                    seed=overall_seed,
                )
            )

        blocks.append(
            {
                "block_kind": "training",
                "block_idx": block_idx,
                "block_id": f"training_block_{block_idx + 1}",
                "block_label": f"Training Block {block_idx + 1}",
                "trials": trials,
                "pair_ids": ["AB", "BC", "CD", "DE"],
                "trial_count": len(trials),
                "criterion_threshold": _coerce_float(
                    getattr(settings, "training_accuracy_threshold", DEFAULT_TRAINING_THRESHOLD),
                    DEFAULT_TRAINING_THRESHOLD,
                ),
            }
        )

    test_block_idx = len(training_keys)
    test_rng = _trial_rng(overall_seed, test_block_idx, 0, salt=29)
    test_sequence = _expand_pattern(test_pattern, rng=test_rng)
    test_trials: list[dict[str, Any]] = []
    for trial_index, pair_id in enumerate(test_sequence, start=1):
        pair_info = pair_map[pair_id]
        if pair_info.get("pair_kind") == "premise":
            condition_id = TEST_PREMISE_CONDITION_ID
        elif str(pair_info.get("probe_name", "")).strip().lower() == "transitive":
            condition_id = TEST_TRANSITIVE_CONDITION_ID
        else:
            condition_id = TEST_ANCHOR_CONDITION_ID
        test_trials.append(
            _trial_spec(
                block_kind="test",
                block_idx=test_block_idx,
                block_label="Final Test",
                trial_index_in_block=trial_index,
                pair_id=pair_id,
                pair_info=pair_info,
                phase="test",
                condition_id=condition_id,
                seed=overall_seed,
            )
        )

    blocks.append(
        {
            "block_kind": "test",
            "block_idx": test_block_idx,
            "block_id": "final_test",
            "block_label": "Final Test",
            "trials": test_trials,
            "pair_ids": ["AB", "BC", "CD", "DE", "BD", "AE"],
            "trial_count": len(test_trials),
            "criterion_threshold": None,
        }
    )

    return blocks


def summarize_trials(trials: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize accuracy and latency across a trial list."""

    total = len(trials)
    correct = 0
    timeouts = 0
    correct_rts: list[float] = []

    for trial in trials:
        if bool(trial.get("response_correct")):
            correct += 1
            rt = trial.get("response_rt")
            if isinstance(rt, (int, float)) and rt > 0:
                correct_rts.append(float(rt))
        if bool(trial.get("timed_out")):
            timeouts += 1

    mean_correct_rt_ms = round((sum(correct_rts) / len(correct_rts)) * 1000.0, 1) if correct_rts else None
    return {
        "total_trials": total,
        "correct_trials": correct,
        "accuracy": (correct / total) if total else 0.0,
        "mean_correct_rt_ms": mean_correct_rt_ms,
        "timeout_count": timeouts,
    }


def summarize_training_block(trials: list[dict[str, Any]], *, threshold: float = DEFAULT_TRAINING_THRESHOLD) -> dict[str, Any]:
    """Summarize premise-pair accuracy for a training block."""

    pair_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    for trial in trials:
        if str(trial.get("pair_kind", "")).strip().lower() != "premise":
            continue
        pair_id = str(trial.get("pair_id", "")).strip().upper()
        if not pair_id:
            continue
        pair_counts[pair_id]["total"] += 1
        if bool(trial.get("response_correct")):
            pair_counts[pair_id]["correct"] += 1

    pair_accuracy: dict[str, float] = {}
    for pair_id, counts in pair_counts.items():
        total = counts["total"]
        pair_accuracy[pair_id] = (counts["correct"] / total) if total else 0.0

    overall = summarize_trials(trials)
    criterion_met = bool(pair_accuracy) and all(acc >= float(threshold) for acc in pair_accuracy.values())
    return {
        **overall,
        "pair_accuracy": pair_accuracy,
        "criterion_met": criterion_met,
        "criterion_threshold": float(threshold),
    }


def summarize_block_trials(trials: list[dict[str, Any]], *, threshold: float = DEFAULT_TRAINING_THRESHOLD) -> dict[str, Any]:
    """Compatibility wrapper used by the task runtime."""

    return summarize_training_block(trials, threshold=threshold)


def format_pair_accuracy_lines(summary: dict[str, Any]) -> str:
    """Render pair accuracy into a compact multi-line summary."""

    pair_accuracy = dict(summary.get("pair_accuracy", {}) or {})
    if not pair_accuracy:
        return "No premise-pair data."

    ordered_pairs = ["AB", "BC", "CD", "DE"]
    lines: list[str] = []
    for pair_id in ordered_pairs:
        if pair_id not in pair_accuracy:
            continue
        lines.append(f"{pair_id}: {pair_accuracy[pair_id] * 100:.0f}%")

    for pair_id, acc in pair_accuracy.items():
        if pair_id not in ordered_pairs:
            lines.append(f"{pair_id}: {acc * 100:.0f}%")

    return "   ".join(lines)
