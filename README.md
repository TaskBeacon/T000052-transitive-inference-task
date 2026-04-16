# Transitive Inference Task

| Field | Value |
|---|---|
| Name | Transitive Inference Task |
| Version | v0.1.0-dev |
| URL / Repository | [TaskBeacon/T000052-transitive-inference-task](https://github.com/TaskBeacon/T000052-transitive-inference-task) |
| Short Description | Classic five-symbol transitive inference task with premise-pair learning, repeat-until-criterion training, and a final BD/AE test |
| Created By | TaskBeacon build pipeline |
| Date Updated | 2026-04-17 |
| PsyFlow Version | 0.1.12 |
| PsychoPy Version | 2025.2.4 |
| Modality | Behavior |
| Language | English |

## 1. Task Overview

This task implements a classic transitive inference paradigm in PsychoPy/PsyFlow. Participants learn a five-symbol Hiragana hierarchy by trial and error across four premise-pair training blocks. The training blocks repeat until every premise pair reaches the accuracy criterion, and the final test block mixes premise pairs with the BD transitive probe and the AE anchor probe.

The runtime keeps the execution auditable. Trial order is deterministic from the task seed, left/right symbol placement is randomized per trial, and training feedback is limited to the learning phase. The task uses text-rendered symbols and does not require external media assets.

## 2. Task Flow

![Task Flow](task_flow.png)

### Block-Level Flow

| Step | Description |
|---|---|
| Load Config | Read the mode-specific config and task metadata. |
| Collect Subject Info | Collect subject ID in human mode or inject deterministic IDs in QA/sim. |
| Initialize Runtime | Create the PsychoPy window, keyboard, triggers, and stimulus bank. |
| Show Instructions | Present the transitive-inference instructions and key mappings. |
| Run Training Block 1 | Present premise pairs with feedback until the criterion is met. |
| Run Training Block 2 | Present the same premise-pair learning structure with a different schedule. |
| Run Training Block 3 | Present the compact premise-pair schedule. |
| Run Training Block 4 | Present the randomized premise-pair schedule. |
| Run Final Test | Present premise, transitive, and anchor probes with no feedback. |
| Finish | Present the goodbye screen, send the end trigger, and quit PsychoPy. |

### Trial-Level Flow

| Step | Description |
|---|---|
| Trial Fixation | Show a centered fixation cross for a short pre-pair interval. |
| Pair Display | Show the two Hiragana symbols side-by-side with a response prompt. |
| Pair Response | Collect `Z` for left or `M` for right within the response window. |
| Training Feedback | Show correctness feedback only during the training blocks. |
| Trial ITI | Show the fixation cross again before the next trial. |

### Controller Logic

| Feature | Description |
|---|---|
| Condition Scheduling | `build_session_plan(...)` expands the config-defined training and test patterns into trial lists. |
| Determinism | Trial order and left/right placement are deterministic from the overall seed, block index, trial index, and block attempt. |
| Criterion Control | Training blocks repeat until every premise pair reaches the accuracy threshold or the repeat limit is reached. |
| Trial Context | Every participant-visible phase in `src/run_trial.py` calls `set_trial_context(...)` before display or response capture. |
| Simulation | The scripted and sampler responders exercise the response path with high-accuracy training behavior and slightly lower transitive-probe accuracy. |

### Other Logic

| Feature | Description |
|---|---|
| Asset Strategy | All stimuli are text-rendered Hiragana glyphs and prompt text; no external media assets are required. |
| Output Capture | Trial data are written to mode-specific CSV files in `outputs/`. |
| Repeat Handling | Failed training blocks are replayed with the same configured schedule. |

## 3. Configuration Summary

All settings are defined in `config/config.yaml`.

### a. Subject Info

| Field | Meaning |
|---|---|
| `subject_id` | Three-digit participant identifier. |

### b. Window Settings

| Parameter | Value |
|---|---|
| `window.size` | `[1280, 720]` |
| `window.units` | `pix` |
| `window.bg_color` | `black` |
| `window.fullscreen` | `false` |
| `window.screen` | `0` |

### c. Stimuli

| Stimulus ID | Purpose |
|---|---|
| `instruction_text` | Intro screen that explains the hierarchy-learning task and key mapping. |
| `training_block_intro_text` | Training block intro screen with criterion reminder. |
| `test_block_intro_text` | Final test intro screen with no-feedback reminder. |
| `pair_prompt_text` | Response prompt displayed beneath the symbol pair. |
| `pair_left_symbol` / `pair_right_symbol` | The two Hiragana glyphs shown on each trial. |
| `fixation` | Center fixation cross used before pair screens and during ITIs. |
| `training_feedback_*` | Training-only feedback screens for correct, incorrect, and timeout outcomes. |
| `block_summary_text` | Training-block summary with pair accuracies and repeat/advance notice. |
| `good_bye_text` | Final summary screen and exit prompt. |

### d. Timing

| Parameter | Value |
|---|---|
| `timing.fixation_duration_s` | `0.4` s |
| `timing.response_window_s` | `3.0` s |
| `timing.feedback_duration_s` | `0.8` s |
| `timing.iti_duration_s` | `0.4` s |

### e. Triggers

| Event | Code |
|---|---|
| `exp_onset` / `exp_end` | `1` / `2` |
| `block_onset` / `block_end` | `10` / `11` |
| `instruction_onset` | `12` |
| `trial_fixation_onset` | `20` |
| `pair_onset` | `21` |
| `response_z` / `response_m` | `31` / `32` |
| `trial_timeout` | `33` |
| `feedback_onset` | `34` |
| `trial_iti_onset` | `35` |
| `good_bye_onset` | `40` |

### f. Adaptive Controller

| Parameter | Value |
|---|---|
| `task.training_accuracy_threshold` | `0.8` |
| `task.block_repeat_limit` | `3` |
| Adaptive controller | Training blocks repeat until the 80% premise-pair criterion is reached or the repeat limit is hit. |

## 4. Methods (for academic publication)

Participants completed a transitive inference task using five Hiragana symbols arranged in a learned hierarchy. They practiced adjacent premise pairs across four training blocks and received trial-level feedback during learning. Once the premise-pair criterion was reached, they moved to a final test block that mixed premise pairs with the novel BD transitive probe and the AE anchor probe.

The executable implementation keeps the protocol auditable. Trial order, randomization, and repeat decisions are deterministic from the config seed and the observed training accuracy. The displayed stimuli are text-rendered Hiragana glyphs, which makes the task portable and easy to localize or restyle without changing the state machine.
