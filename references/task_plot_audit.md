# Task Plot Audit

- generated_at: 2026-04-17T01:31:58
- mode: existing
- task_path: E:\Taskbeacon\T000052-transitive-inference-task

## 1. Inputs and provenance

- E:\Taskbeacon\T000052-transitive-inference-task\README.md
- E:\Taskbeacon\T000052-transitive-inference-task\config\config.yaml
- E:\Taskbeacon\T000052-transitive-inference-task\src\run_trial.py

## 2. Evidence extracted from README

- | Step | Description |
- |---|---|
- | Trial Fixation | Show a centered fixation cross for a short pre-pair interval. |
- | Pair Display | Show the two Hiragana symbols side-by-side with a response prompt. |
- | Pair Response | Collect `Z` for left or `M` for right within the response window. |
- | Training Feedback | Show correctness feedback only during the training blocks. |
- | Trial ITI | Show the fixation cross again before the next trial. |

## 3. Evidence extracted from config/source

- training_premise: phase=fixation phase, deadline_expr=fixation_duration_s, response_expr=n/a, stim_expr='fixation'
- training_premise: phase=pair phase, deadline_expr=response_window_s, response_expr=n/a, stim_expr='pair_display'
- training_premise: phase=training feedback, deadline_expr=feedback_duration_s, response_expr=n/a, stim_expr=feedback_name
- training_premise: phase=iti phase, deadline_expr=iti_duration_s, response_expr=n/a, stim_expr='fixation'
- test_premise: phase=fixation phase, deadline_expr=fixation_duration_s, response_expr=n/a, stim_expr='fixation'
- test_premise: phase=pair phase, deadline_expr=response_window_s, response_expr=n/a, stim_expr='pair_display'
- test_premise: phase=training feedback, deadline_expr=feedback_duration_s, response_expr=n/a, stim_expr=feedback_name
- test_premise: phase=iti phase, deadline_expr=iti_duration_s, response_expr=n/a, stim_expr='fixation'
- test_transitive: phase=fixation phase, deadline_expr=fixation_duration_s, response_expr=n/a, stim_expr='fixation'
- test_transitive: phase=pair phase, deadline_expr=response_window_s, response_expr=n/a, stim_expr='pair_display'
- test_transitive: phase=training feedback, deadline_expr=feedback_duration_s, response_expr=n/a, stim_expr=feedback_name
- test_transitive: phase=iti phase, deadline_expr=iti_duration_s, response_expr=n/a, stim_expr='fixation'
- test_anchor: phase=fixation phase, deadline_expr=fixation_duration_s, response_expr=n/a, stim_expr='fixation'
- test_anchor: phase=pair phase, deadline_expr=response_window_s, response_expr=n/a, stim_expr='pair_display'
- test_anchor: phase=training feedback, deadline_expr=feedback_duration_s, response_expr=n/a, stim_expr=feedback_name
- test_anchor: phase=iti phase, deadline_expr=iti_duration_s, response_expr=n/a, stim_expr='fixation'

## 4. Mapping to task_plot_spec

- timeline collection: one representative timeline per unique trial logic
- phase flow inferred from run_trial set_trial_context order and branch predicates
- participant-visible show() phases without set_trial_context are inferred where possible and warned
- duration/response inferred from deadline/capture expressions
- stimulus examples inferred from stim_id + config stimuli
- conditions with equivalent phase/timing logic collapsed and annotated as variants
- root_key: task_plot_spec
- spec_version: 0.2

## 5. Style decision and rationale

- Single timeline-collection view selected by policy: one representative condition per unique timeline logic.

## 6. Rendering parameters and constraints

- output_file: task_flow.png
- dpi: 300
- max_conditions: 4
- screens_per_timeline: 6
- screen_overlap_ratio: 0.1
- screen_slope: 0.08
- screen_slope_deg: 25.0
- screen_aspect_ratio: 1.4545454545454546
- qa_mode: local
- auto_layout_feedback:
  - layout pass 1: crop-only; left=0.030, right=0.032, blank=0.118
- auto_layout_feedback_records:
  - pass: 1
    metrics: {'left_ratio': 0.0295, 'right_ratio': 0.0315, 'blank_ratio': 0.1182}
- validator_warnings:
  - timelines[0].phases[1] missing duration_ms; renderer will annotate as n/a.
  - timelines[0].phases[2] missing duration_ms; renderer will annotate as n/a.
  - timelines[0].phases[3] missing duration_ms; renderer will annotate as n/a.

## 7. Output files and checksums

- E:\Taskbeacon\T000052-transitive-inference-task\references\task_plot_spec.yaml: sha256=b42a55c9f7954370ed3a7e473efd7ea429966b2086793ca779a3d04ff5dbd83f
- E:\Taskbeacon\T000052-transitive-inference-task\references\task_plot_spec.json: sha256=0f3f868641d90d6582e0bed49b7af49fec0ffdd1a768f36e4d5514e48a9478a3
- E:\Taskbeacon\T000052-transitive-inference-task\references\task_plot_source_excerpt.md: sha256=9d909b59650e0b794edd747356089c381750e72499b3f2115b4573bd73312d5f
- E:\Taskbeacon\T000052-transitive-inference-task\task_flow.png: sha256=9097ecbd92bb70f093822eddc52e8fefb70cf5287caf7e7a57b60cc187f8a710

## 8. Inferred/uncertain items

- training_premise:fixation phase:heuristic range parse from '_coerce_float(getattr(settings, 'fixation_duration_s', 0.4), 0.4)'
- training_premise:pair phase:unable to resolve duration from '_coerce_float(getattr(settings, 'response_window_s', DEFAULT_RESPONSE_WINDOW_S), DEFAULT_RESPONSE_WINDOW_S)'
- training_premise:training feedback:unable to resolve duration from '_coerce_float(getattr(settings, 'feedback_duration_s', DEFAULT_FEEDBACK_DURATION_S), DEFAULT_FEEDBACK_DURATION_S)'
- training_premise:iti phase:unable to resolve duration from '_coerce_float(getattr(settings, 'iti_duration_s', DEFAULT_ITI_DURATION_S), DEFAULT_ITI_DURATION_S)'
- test_premise:fixation phase:heuristic range parse from '_coerce_float(getattr(settings, 'fixation_duration_s', 0.4), 0.4)'
- test_premise:pair phase:unable to resolve duration from '_coerce_float(getattr(settings, 'response_window_s', DEFAULT_RESPONSE_WINDOW_S), DEFAULT_RESPONSE_WINDOW_S)'
- test_premise:training feedback:unable to resolve duration from '_coerce_float(getattr(settings, 'feedback_duration_s', DEFAULT_FEEDBACK_DURATION_S), DEFAULT_FEEDBACK_DURATION_S)'
- test_premise:iti phase:unable to resolve duration from '_coerce_float(getattr(settings, 'iti_duration_s', DEFAULT_ITI_DURATION_S), DEFAULT_ITI_DURATION_S)'
- test_transitive:fixation phase:heuristic range parse from '_coerce_float(getattr(settings, 'fixation_duration_s', 0.4), 0.4)'
- test_transitive:pair phase:unable to resolve duration from '_coerce_float(getattr(settings, 'response_window_s', DEFAULT_RESPONSE_WINDOW_S), DEFAULT_RESPONSE_WINDOW_S)'
- test_transitive:training feedback:unable to resolve duration from '_coerce_float(getattr(settings, 'feedback_duration_s', DEFAULT_FEEDBACK_DURATION_S), DEFAULT_FEEDBACK_DURATION_S)'
- test_transitive:iti phase:unable to resolve duration from '_coerce_float(getattr(settings, 'iti_duration_s', DEFAULT_ITI_DURATION_S), DEFAULT_ITI_DURATION_S)'
- test_anchor:fixation phase:heuristic range parse from '_coerce_float(getattr(settings, 'fixation_duration_s', 0.4), 0.4)'
- test_anchor:pair phase:unable to resolve duration from '_coerce_float(getattr(settings, 'response_window_s', DEFAULT_RESPONSE_WINDOW_S), DEFAULT_RESPONSE_WINDOW_S)'
- test_anchor:training feedback:unable to resolve duration from '_coerce_float(getattr(settings, 'feedback_duration_s', DEFAULT_FEEDBACK_DURATION_S), DEFAULT_FEEDBACK_DURATION_S)'
- test_anchor:iti phase:unable to resolve duration from '_coerce_float(getattr(settings, 'iti_duration_s', DEFAULT_ITI_DURATION_S), DEFAULT_ITI_DURATION_S)'
- collapsed equivalent condition logic into representative timeline: training_premise, test_premise, test_transitive, test_anchor
- unparsed if-tests defaulted to condition-agnostic applicability: block_kind == 'training'; response_correct; rng.random() < 0.5; timed_out
