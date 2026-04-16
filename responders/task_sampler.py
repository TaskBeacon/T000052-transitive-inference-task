from __future__ import annotations

import random as _py_random
from dataclasses import dataclass
from typing import Any

from psyflow.sim.contracts import Action, Feedback, Observation, SessionInfo


@dataclass
class TaskSamplerResponder:
    """Task-specific simulation responder for the transitive-inference task."""

    key: str | None = None
    premise_hit_rate: float = 0.98
    test_premise_hit_rate: float = 0.95
    test_transitive_hit_rate: float = 0.88
    test_anchor_hit_rate: float = 0.93
    timeout_rate: float = 0.02
    rt_mean_s: float = 0.95
    rt_sd_s: float = 0.22
    rt_min_s: float = 0.18
    continue_rt_s: float = 0.5

    def __post_init__(self) -> None:
        self._rng: Any = None
        self.premise_hit_rate = max(0.0, min(1.0, float(self.premise_hit_rate)))
        self.test_premise_hit_rate = max(0.0, min(1.0, float(self.test_premise_hit_rate)))
        self.test_transitive_hit_rate = max(0.0, min(1.0, float(self.test_transitive_hit_rate)))
        self.test_anchor_hit_rate = max(0.0, min(1.0, float(self.test_anchor_hit_rate)))
        self.timeout_rate = max(0.0, min(1.0, float(self.timeout_rate)))
        self.rt_mean_s = float(self.rt_mean_s)
        self.rt_sd_s = max(1e-6, float(self.rt_sd_s))
        self.rt_min_s = max(0.0, float(self.rt_min_s))
        self.continue_rt_s = max(self.rt_min_s, float(self.continue_rt_s))

    def start_session(self, session: SessionInfo, rng: Any) -> None:
        self._rng = rng

    def on_feedback(self, fb: Feedback) -> None:
        return None

    def end_session(self) -> None:
        self._rng = None

    def _sample_normal(self, mean: float, sd: float) -> float:
        rng = self._rng
        if hasattr(rng, "normal"):
            return float(rng.normal(mean, sd))
        return float(rng.gauss(mean, sd))

    def _sample_random(self) -> float:
        rng = self._rng
        if hasattr(rng, "random"):
            return float(rng.random())
        return float(_py_random.random())

    def _pick_valid_key(self, valid_keys: list[str], correct_key: str | None) -> str | None:
        if correct_key and correct_key in valid_keys:
            return correct_key
        if self.key and self.key in valid_keys:
            return self.key
        return valid_keys[0] if valid_keys else None

    def _profile(self, obs: Observation) -> dict[str, Any]:
        task_factors = dict(getattr(obs, "task_factors", {}) or {})
        if not task_factors and isinstance(getattr(obs, "extras", None), dict):
            task_factors = dict(obs.extras.get("task_factors", {}) or {})

        stage = str(task_factors.get("stage", getattr(obs, "phase", ""))).strip().lower()
        condition_id = str(task_factors.get("condition_id", "")).strip().lower()
        block_idx = int(task_factors.get("block_idx", 0) or 0)

        if any(
            token in f"{stage} {condition_id}"
            for token in ("instruction", "block_intro", "block_summary", "good_bye")
        ):
            return {
                "task_factors": task_factors,
                "stage": stage,
                "condition_id": condition_id,
                "hit_rate": 1.0,
                "timeout_rate": 0.0,
                "rt_mean_s": self.continue_rt_s,
            }

        if condition_id == "training_premise":
            hit_rate = self.premise_hit_rate + min(0.01 * max(block_idx - 1, 0), 0.02)
            timeout_rate = max(0.0, self.timeout_rate - 0.01)
            rt_mean = max(self.rt_min_s, self.rt_mean_s - 0.1)
        elif condition_id == "test_premise":
            hit_rate = self.test_premise_hit_rate
            timeout_rate = self.timeout_rate
            rt_mean = self.rt_mean_s
        elif condition_id == "test_transitive":
            hit_rate = self.test_transitive_hit_rate
            timeout_rate = self.timeout_rate + 0.01
            rt_mean = self.rt_mean_s + 0.15
        elif condition_id == "test_anchor":
            hit_rate = self.test_anchor_hit_rate
            timeout_rate = self.timeout_rate
            rt_mean = self.rt_mean_s + 0.05
        else:
            hit_rate = self.premise_hit_rate
            timeout_rate = self.timeout_rate
            rt_mean = self.rt_mean_s

        if block_idx >= 2 and condition_id in {"training_premise", "test_premise"}:
            hit_rate += 0.01

        return {
            "task_factors": task_factors,
            "stage": stage,
            "condition_id": condition_id,
            "hit_rate": max(0.0, min(1.0, hit_rate)),
            "timeout_rate": max(0.0, min(1.0, timeout_rate)),
            "rt_mean_s": max(self.rt_min_s, rt_mean),
        }

    def act(self, obs: Observation) -> Action:
        valid_keys = [str(key) for key in list(obs.valid_keys or [])]
        if not valid_keys:
            return Action(key=None, rt_s=None, meta={"source": "task_sampler", "reason": "no_valid_keys"})

        rng = self._rng
        if rng is None:
            return Action(key=None, rt_s=None, meta={"source": "task_sampler", "reason": "rng_missing"})

        profile = self._profile(obs)
        task_factors = profile["task_factors"]
        correct_key = task_factors.get("correct_key") or getattr(obs, "correct_key", None)
        correct_key = str(correct_key) if correct_key is not None else None

        if profile["hit_rate"] >= 1.0 and profile["timeout_rate"] <= 0.0:
            rt = max(self.rt_min_s, self._sample_normal(self.continue_rt_s, self.rt_sd_s))
            chosen_key = self._pick_valid_key(valid_keys, correct_key or self.key)
            return Action(
                key=chosen_key,
                rt_s=rt,
                meta={"source": "task_sampler", "outcome": "continue", "correct_key": correct_key, "stage": profile["stage"]},
            )

        if self._sample_random() < profile["timeout_rate"]:
            return Action(
                key=None,
                rt_s=None,
                meta={"source": "task_sampler", "outcome": "timeout", "correct_key": correct_key, "stage": profile["stage"]},
            )

        rt = max(self.rt_min_s, self._sample_normal(profile["rt_mean_s"], self.rt_sd_s))

        if self._sample_random() > profile["hit_rate"]:
            wrong_keys = [key for key in valid_keys if key != correct_key]
            chosen_key = wrong_keys[0] if wrong_keys else self._pick_valid_key(valid_keys, correct_key)
            return Action(
                key=chosen_key,
                rt_s=rt,
                meta={"source": "task_sampler", "outcome": "miss", "correct_key": correct_key, "stage": profile["stage"]},
            )

        chosen_key = self._pick_valid_key(valid_keys, correct_key)
        return Action(
            key=chosen_key,
            rt_s=rt,
            meta={"source": "task_sampler", "outcome": "hit", "correct_key": correct_key, "stage": profile["stage"]},
        )
