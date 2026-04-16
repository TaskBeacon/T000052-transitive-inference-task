from contextlib import nullcontext
from pathlib import Path

import pandas as pd
from psychopy import core

from psyflow import (
    StimBank,
    StimUnit,
    SubInfo,
    TaskSettings,
    context_from_config,
    initialize_exp,
    initialize_triggers,
    load_config,
    parse_task_run_options,
    runtime_context,
    set_trial_context,
)

from src.run_trial import run_trial
from src.utils import (
    DEFAULT_BLOCK_REPEAT_LIMIT,
    DEFAULT_CONTINUE_KEY,
    DEFAULT_TRAINING_THRESHOLD,
    build_session_plan,
    format_pair_accuracy_lines,
    summarize_block_trials,
    summarize_trials,
)

MODES = ("human", "qa", "sim")
DEFAULT_CONFIG_BY_MODE = {
    "human": "config/config.yaml",
    "qa": "config/config_qa.yaml",
    "sim": "config/config_scripted_sim.yaml",
}


def _show_text(
    stim_bank: StimBank,
    win,
    kb,
    runtime,
    stim_name: str,
    *,
    phase: str,
    trial_id: str,
    block_id: str,
    condition_id: str,
    valid_keys: list[str],
    task_factors: dict | None = None,
    **fmt_kwargs,
) -> None:
    unit = StimUnit(stim_name, win, kb, runtime=runtime).add_stim(
        stim_bank.get_and_format(stim_name, **fmt_kwargs)
    )
    set_trial_context(
        unit,
        trial_id=trial_id,
        phase=phase,
        deadline_s=None,
        valid_keys=list(valid_keys),
        block_id=block_id,
        condition_id=condition_id,
        task_factors=task_factors or {},
        stim_id=stim_name,
    )
    unit.wait_and_continue(keys=list(valid_keys))


def _format_pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.1f}%"


def _format_ms(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value:.1f} ms"


def _run_block(
    *,
    win,
    kb,
    settings,
    stim_bank: StimBank,
    trigger_runtime,
    block_plan: dict,
    all_data: list[dict],
    continue_key: list[str],
    repeat_limit: int,
    threshold: float,
) -> None:
    block_kind = str(block_plan["block_kind"])
    block_label = str(block_plan["block_label"])
    block_idx = int(block_plan["block_idx"])
    block_id = str(block_plan["block_id"])
    block_trials = list(block_plan["trials"])

    if block_kind == "training":
        block_attempt = 0
        while True:
            block_attempt += 1
            attempt_block_id = f"{block_id}_attempt_{block_attempt}"
            trigger_runtime.send(settings.triggers.get("block_onset"))
            _show_text(
                stim_bank,
                win,
                kb,
                trigger_runtime,
                "training_block_intro_text",
                phase="block_intro",
                trial_id=f"{attempt_block_id}_intro",
                block_id=attempt_block_id,
                condition_id="training_block",
                valid_keys=continue_key,
                task_factors={
                    "stage": "block_intro",
                    "block_kind": block_kind,
                    "block_label": block_label,
                    "block_idx": block_idx,
                    "block_attempt": block_attempt,
                    "trial_count": len(block_trials),
                    "threshold": threshold,
                    "repeat_limit": repeat_limit,
                },
                block_label=block_label,
                trial_count=len(block_trials),
                threshold_pct=f"{threshold * 100:.0f}%",
                repeat_limit=repeat_limit,
            )

            attempt_trials: list[dict] = []
            for trial_spec in block_trials:
                trial_data = run_trial(
                    win,
                    kb,
                    settings,
                    condition={**trial_spec, "block_attempt": block_attempt},
                    stim_bank=stim_bank,
                    trigger_runtime=trigger_runtime,
                    block_id=attempt_block_id,
                    block_idx=block_idx,
                )
                attempt_trials.append(trial_data)
                all_data.append(trial_data)

            summary = summarize_block_trials(attempt_trials, threshold=threshold)
            trigger_runtime.send(settings.triggers.get("block_end"))

            repeat_block = (not summary["criterion_met"]) and (block_attempt < repeat_limit)
            if summary["criterion_met"]:
                repeat_message = f"All premise pairs reached {threshold * 100:.0f}% accuracy. Continue to the next block."
            elif repeat_block:
                repeat_message = "This block will repeat now so the premise pairs can be learned more firmly."
            else:
                repeat_message = "Repeat limit reached. Continue to the next block."

            _show_text(
                stim_bank,
                win,
                kb,
                trigger_runtime,
                "block_summary_text",
                phase="block_summary",
                trial_id=f"{attempt_block_id}_summary",
                block_id=attempt_block_id,
                condition_id="training_block",
                valid_keys=continue_key,
                task_factors={
                    "stage": "block_summary",
                    "block_kind": block_kind,
                    "block_label": block_label,
                    "block_idx": block_idx,
                    "block_attempt": block_attempt,
                    "criterion_met": summary["criterion_met"],
                    "threshold": threshold,
                    "repeat_limit": repeat_limit,
                    "repeat_message": repeat_message,
                    "overall_accuracy": summary["accuracy"],
                    "timeout_count": summary["timeout_count"],
                },
                block_label=block_label,
                pair_accuracy_lines=format_pair_accuracy_lines(summary),
                repeat_message=repeat_message,
            )

            if not repeat_block:
                break
    else:
        trigger_runtime.send(settings.triggers.get("block_onset"))
        _show_text(
            stim_bank,
            win,
            kb,
            trigger_runtime,
            "test_block_intro_text",
            phase="block_intro",
            trial_id=f"{block_id}_intro",
            block_id=block_id,
            condition_id="test_block",
            valid_keys=continue_key,
            task_factors={
                "stage": "block_intro",
                "block_kind": block_kind,
                "block_label": block_label,
                "block_idx": block_idx,
                "trial_count": len(block_trials),
            },
            block_label=block_label,
            trial_count=len(block_trials),
        )

        for trial_spec in block_trials:
            trial_data = run_trial(
                win,
                kb,
                settings,
                condition={**trial_spec, "block_attempt": 1},
                stim_bank=stim_bank,
                trigger_runtime=trigger_runtime,
                block_id=block_id,
                block_idx=block_idx,
            )
            all_data.append(trial_data)

        trigger_runtime.send(settings.triggers.get("block_end"))


def run(options):
    """Run the transitive-inference task in human, QA, or sim mode."""

    task_root = Path(__file__).resolve().parent
    cfg = load_config(str(options.config_path))

    output_dir: Path | None = None
    runtime_scope = nullcontext()
    runtime_ctx = None
    if options.mode in ("qa", "sim"):
        runtime_ctx = context_from_config(task_dir=task_root, config=cfg, mode=options.mode)
        output_dir = runtime_ctx.output_dir
        runtime_scope = runtime_context(runtime_ctx)

    with runtime_scope:
        if options.mode == "qa":
            subject_data = {"subject_id": "qa"}
        elif options.mode == "sim":
            participant_id = "sim"
            if runtime_ctx is not None and runtime_ctx.session is not None:
                participant_id = str(runtime_ctx.session.participant_id or "sim")
            subject_data = {"subject_id": participant_id}
        else:
            subform = SubInfo(cfg["subform_config"])
            subject_data = subform.collect()

        settings = TaskSettings.from_dict(cfg["task_config"])
        if options.mode in ("qa", "sim") and output_dir is not None:
            settings.save_path = str(output_dir)
        settings.add_subinfo(subject_data)

        if options.mode == "qa" and output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            settings.res_file = str(output_dir / "qa_trace.csv")
            settings.log_file = str(output_dir / "qa_psychopy.log")
            settings.json_file = str(output_dir / "qa_settings.json")
        elif options.mode == "sim" and output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)
            settings.res_file = str(output_dir / "sim_trace.csv")
            settings.log_file = str(output_dir / "sim_psychopy.log")
            settings.json_file = str(output_dir / "sim_settings.json")

        settings.triggers = cfg["trigger_config"]
        trigger_runtime = initialize_triggers(mock=True) if options.mode in ("qa", "sim") else initialize_triggers(cfg)

        win, kb = initialize_exp(settings)
        stim_bank = StimBank(win, cfg["stim_config"]).preload_all()
        settings.save_to_json()

        continue_key = [str(getattr(settings, "continue_key", DEFAULT_CONTINUE_KEY)).strip().lower()]
        repeat_limit = int(getattr(settings, "block_repeat_limit", DEFAULT_BLOCK_REPEAT_LIMIT))
        threshold = float(getattr(settings, "training_accuracy_threshold", DEFAULT_TRAINING_THRESHOLD))

        trigger_runtime.send(settings.triggers.get("exp_onset"))
        _show_text(
            stim_bank,
            win,
            kb,
            trigger_runtime,
            "instruction_text",
            phase="instruction",
            trial_id="instruction",
            block_id="instruction",
            condition_id="instruction",
            valid_keys=continue_key,
            task_factors={
                "stage": "instruction",
                "repeat_limit": repeat_limit,
                "training_threshold": threshold,
            },
            chain_symbols=" ".join(str(x) for x in list(getattr(settings, "chain_symbols", []))),
            training_threshold_pct=f"{threshold * 100:.0f}%",
            repeat_limit=repeat_limit,
        )

        session_plan = build_session_plan(settings)
        all_data: list[dict] = []

        for block_plan in session_plan:
            _run_block(
                win=win,
                kb=kb,
                settings=settings,
                stim_bank=stim_bank,
                trigger_runtime=trigger_runtime,
                block_plan=block_plan,
                all_data=all_data,
                continue_key=continue_key,
                repeat_limit=repeat_limit,
                threshold=threshold,
            )

        total_summary = summarize_trials(all_data)
        trigger_runtime.send(settings.triggers.get("good_bye_onset"))
        _show_text(
            stim_bank,
            win,
            kb,
            trigger_runtime,
            "good_bye_text",
            phase="good_bye",
            trial_id="good_bye",
            block_id="good_bye",
            condition_id="good_bye",
            valid_keys=continue_key,
            task_factors={
                "stage": "good_bye",
                "overall_accuracy": total_summary["accuracy"],
                "mean_correct_rt_ms": total_summary["mean_correct_rt_ms"],
                "timeout_count": total_summary["timeout_count"],
            },
            overall_accuracy_pct=_format_pct(total_summary["accuracy"]),
            mean_correct_rt_ms=_format_ms(total_summary["mean_correct_rt_ms"]),
            timeout_count=int(total_summary["timeout_count"]),
        )

        trigger_runtime.send(settings.triggers.get("exp_end"))
        pd.DataFrame(all_data).to_csv(settings.res_file, index=False)

        trigger_runtime.close()
        core.quit()


def main() -> None:
    task_root = Path(__file__).resolve().parent
    options = parse_task_run_options(
        task_root=task_root,
        description="Run task in human/qa/sim mode.",
        default_config_by_mode=DEFAULT_CONFIG_BY_MODE,
        modes=MODES,
    )
    run(options)


if __name__ == "__main__":
    main()
