from __future__ import annotations

import random
from functools import partial
from typing import Any

from psyflow import StimUnit, next_trial_id, set_trial_context

from src.utils import (
    DEFAULT_FEEDBACK_DURATION_S,
    DEFAULT_ITI_DURATION_S,
    DEFAULT_LEFT_KEY,
    DEFAULT_RIGHT_KEY,
    DEFAULT_RESPONSE_WINDOW_S,
)


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return float(default)


def _parse_response_key(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _trial_rng(seed: int, block_idx: int, trial_index_in_block: int, attempt_idx: int, salt: int = 0) -> random.Random:
    mixed = (
        (int(seed) + 1) * 1_000_003
        + (int(block_idx) + 1) * 10_009
        + (int(trial_index_in_block) + 1) * 1_009
        + (int(attempt_idx) + 1) * 97
        + int(salt) * 31
    )
    return random.Random(mixed % (2**32))


def _response_trigger_map(settings: Any, left_key: str, right_key: str) -> dict[str, Any]:
    trigger_map = getattr(settings, "triggers", {}) or {}
    return {
        left_key: trigger_map.get(f"response_{left_key}"),
        right_key: trigger_map.get(f"response_{right_key}"),
    }


def _selected_symbol(left_symbol: str, right_symbol: str, response_key: str, left_key: str, right_key: str) -> str:
    if response_key == left_key:
        return left_symbol
    if response_key == right_key:
        return right_symbol
    return ""


def run_trial(
    win,
    kb,
    settings,
    condition,
    stim_bank,
    trigger_runtime,
    block_id=None,
    block_idx=None,
):
    """Run one transitive-inference trial."""

    trial_id = int(next_trial_id())
    trial_spec = dict(condition or {})
    phase = str(trial_spec.get("trial_phase", "training")).strip().lower()
    block_kind = str(trial_spec.get("block_kind", "training")).strip().lower()
    block_id_val = str(block_id) if block_id is not None else str(trial_spec.get("block_id", "block_0"))
    block_idx_val = int(block_idx) if block_idx is not None else int(trial_spec.get("block_idx", 0))
    block_attempt = int(trial_spec.get("block_attempt", 1))
    block_label = str(trial_spec.get("block_label", block_id_val))
    pair_id = str(trial_spec.get("pair_id", "")).strip().upper()
    condition_id = str(trial_spec.get("condition_id", phase)).strip()
    pair_kind = str(trial_spec.get("pair_kind", "premise")).strip().lower()
    correct_symbol = str(trial_spec.get("correct_symbol", "")).strip()
    foil_symbol = str(trial_spec.get("foil_symbol", "")).strip()
    seed = int(trial_spec.get("seed", getattr(settings, "overall_seed", 52052)))

    left_key = str(getattr(settings, "left_key", DEFAULT_LEFT_KEY)).strip().lower()
    right_key = str(getattr(settings, "right_key", DEFAULT_RIGHT_KEY)).strip().lower()
    response_window_s = _coerce_float(getattr(settings, "response_window_s", DEFAULT_RESPONSE_WINDOW_S), DEFAULT_RESPONSE_WINDOW_S)
    feedback_duration_s = _coerce_float(getattr(settings, "feedback_duration_s", DEFAULT_FEEDBACK_DURATION_S), DEFAULT_FEEDBACK_DURATION_S)
    iti_duration_s = _coerce_float(getattr(settings, "iti_duration_s", DEFAULT_ITI_DURATION_S), DEFAULT_ITI_DURATION_S)
    fixation_duration_s = _coerce_float(getattr(settings, "fixation_duration_s", 0.4), 0.4)

    rng = _trial_rng(seed, block_idx_val, int(trial_spec.get("trial_index_in_block", 0)), block_attempt, salt=13 if phase == "training" else 23)
    if rng.random() < 0.5:
        left_symbol = correct_symbol
        right_symbol = foil_symbol
        correct_side = "left"
        correct_key = left_key
    else:
        left_symbol = foil_symbol
        right_symbol = correct_symbol
        correct_side = "right"
        correct_key = right_key

    trial_data: dict[str, Any] = {
        "trial_id": trial_id,
        "trial_index_in_block": int(trial_spec.get("trial_index_in_block", 0)),
        "block_id": block_id_val,
        "block_idx": block_idx_val,
        "block_attempt": block_attempt,
        "block_kind": block_kind,
        "block_label": block_label,
        "pair_id": pair_id,
        "pair_kind": pair_kind,
        "condition_id": condition_id,
        "trial_phase": phase,
        "correct_symbol": correct_symbol,
        "foil_symbol": foil_symbol,
        "left_symbol": left_symbol,
        "right_symbol": right_symbol,
        "correct_side": correct_side,
        "correct_key": correct_key,
        "stimulus_summary": str(trial_spec.get("stimulus_summary", "")),
        "responded": False,
        "response_key": "",
        "response_rt": None,
        "response_correct": False,
        "timed_out": False,
        "selected_symbol": "",
    }

    make_unit = partial(StimUnit, win=win, kb=kb, runtime=trigger_runtime)

    fixation_phase = "training_fixation" if block_kind == "training" else "test_fixation"
    pair_phase = "training_pair_display" if block_kind == "training" else "test_pair_display"
    iti_phase = "training_iti" if block_kind == "training" else "test_iti"

    # Pre-pair fixation.
    fixation_unit = make_unit(unit_label="trial_fixation").add_stim(stim_bank.get("fixation"))
    set_trial_context(
        fixation_unit,
        trial_id=trial_id,
        phase=fixation_phase,
        deadline_s=fixation_duration_s,
        valid_keys=[],
        block_id=block_id_val,
        condition_id=condition_id,
        task_factors={
            "stage": fixation_phase,
            "block_kind": block_kind,
            "block_label": block_label,
            "block_idx": block_idx_val,
            "block_attempt": block_attempt,
            "pair_id": pair_id,
            "pair_kind": pair_kind,
            "condition_id": condition_id,
        },
        stim_id="fixation",
    )
    fixation_unit.show(
        duration=fixation_duration_s,
        onset_trigger=settings.triggers.get("trial_fixation_onset"),
    ).to_dict(trial_data)

    # Pair choice screen.
    pair_unit = make_unit(unit_label="pair_display")
    pair_unit.add_stim(stim_bank.get_and_format("pair_left_symbol", symbol=left_symbol))
    pair_unit.add_stim(stim_bank.get_and_format("pair_right_symbol", symbol=right_symbol))
    pair_unit.add_stim(stim_bank.get("pair_prompt_text"))
    set_trial_context(
        pair_unit,
        trial_id=trial_id,
        phase=pair_phase,
        deadline_s=response_window_s,
        valid_keys=[left_key, right_key],
        block_id=block_id_val,
        condition_id=condition_id,
        task_factors={
            "stage": pair_phase,
            "block_kind": block_kind,
            "block_label": block_label,
            "block_idx": block_idx_val,
            "block_attempt": block_attempt,
            "pair_id": pair_id,
            "pair_kind": pair_kind,
            "condition_id": condition_id,
            "correct_key": correct_key,
            "correct_side": correct_side,
            "left_symbol": left_symbol,
            "right_symbol": right_symbol,
            "response_window_s": response_window_s,
        },
        stim_id="pair_display",
    )
    pair_unit.capture_response(
        keys=[left_key, right_key],
        correct_keys=[correct_key],
        duration=response_window_s,
        onset_trigger=settings.triggers.get("pair_onset"),
        response_trigger=_response_trigger_map(settings, left_key, right_key),
        timeout_trigger=settings.triggers.get("trial_timeout"),
    ).to_dict(trial_data)

    response_key = _parse_response_key(pair_unit.get_state("response", None))
    response_rt = pair_unit.get_state("rt", None)
    response_correct = bool(response_key and response_key == correct_key)
    timed_out = response_key == ""
    selected_symbol = _selected_symbol(left_symbol, right_symbol, response_key, left_key, right_key)

    trial_data.update(
        {
            "responded": bool(response_key),
            "response_key": response_key,
            "response_rt": float(response_rt) if isinstance(response_rt, (int, float)) else None,
            "response_correct": response_correct,
            "timed_out": timed_out,
            "selected_symbol": selected_symbol,
        }
    )

    # Training feedback only.
    if block_kind == "training":
        if timed_out:
            feedback_name = "training_feedback_timeout"
        elif response_correct:
            feedback_name = "training_feedback_correct"
        else:
            feedback_name = "training_feedback_incorrect"

        feedback_unit = make_unit(unit_label="training_feedback").add_stim(
            stim_bank.get(feedback_name)
        )
        set_trial_context(
            feedback_unit,
            trial_id=trial_id,
            phase="training_feedback",
            deadline_s=feedback_duration_s,
            valid_keys=[],
            block_id=block_id_val,
            condition_id=condition_id,
            task_factors={
                "stage": "training_feedback",
                "block_kind": block_kind,
                "block_label": block_label,
                "block_idx": block_idx_val,
                "block_attempt": block_attempt,
                "pair_id": pair_id,
                "pair_kind": pair_kind,
                "condition_id": condition_id,
                "correct_key": correct_key,
                "response_key": response_key,
                "response_correct": response_correct,
                "timed_out": timed_out,
            },
            stim_id=feedback_name,
        )
        feedback_unit.show(
            duration=feedback_duration_s,
            onset_trigger=settings.triggers.get("feedback_onset"),
        ).to_dict(trial_data)

    # Inter-trial fixation.
    iti_unit = make_unit(unit_label="trial_iti").add_stim(stim_bank.get("fixation"))
    set_trial_context(
        iti_unit,
        trial_id=trial_id,
        phase=iti_phase,
        deadline_s=iti_duration_s,
        valid_keys=[],
        block_id=block_id_val,
        condition_id=condition_id,
        task_factors={
            "stage": iti_phase,
            "block_kind": block_kind,
            "block_label": block_label,
            "block_idx": block_idx_val,
            "block_attempt": block_attempt,
            "pair_id": pair_id,
            "pair_kind": pair_kind,
            "condition_id": condition_id,
        },
        stim_id="fixation",
    )
    iti_unit.show(
        duration=iti_duration_s,
        onset_trigger=settings.triggers.get("trial_iti_onset"),
    ).to_dict(trial_data)

    return trial_data
