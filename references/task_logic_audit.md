# Task Logic Audit

## 1. Paradigm Intent

- Task: Transitive Inference Task
- Primary construct: inferential reasoning over a learned hierarchical order
- Manipulated factors:
  - training phase versus test phase
  - premise pairs versus novel inference/control pairs
  - feedback present versus absent
  - randomized left/right position of the correct symbol
  - training block ordering schedule
- Dependent measures:
  - premise-pair accuracy by training block
  - final premise-pair accuracy at test
  - transitive pair (BD) accuracy
  - end-anchor pair (AE) accuracy
  - response time
  - timeout rate
- Key citations:
  - W2093778263, `Relational learning with and without awareness: Transitive inference using nonverbal stimuli in humans`
  - W2116209672, `Frontal and Parietal Lobe Activation during Transitive Inference in Humans`
  - W2609154042, `A map of abstract relational knowledge in the human hippocampal–entorhinal cortex`
  - W2164512113, `Representation of stable social dominance relations by human infants`

## 2. Block/Trial Workflow

### Block Structure

- Total blocks: 5 nominal blocks in the human profile
  - 4 training blocks
  - 1 final test block
- Trials per block:
  - Training blocks: 40 trials each
  - Test block: 48 trials total
- Randomization/counterbalancing:
  - Left/right screen position of the correct choice is randomized on every trial.
  - Training block 4 uses randomized trial order with equal frequency of all premise pairs.
  - Test block randomizes all 48 trials while preserving 8 repeats per pair type.
- Condition weight policy:
  - `task.condition_weights` is `null` in config.
  - Condition selection is not driven by weighted label sampling.
- Condition generation method:
  - Custom generator.
  - The task uses cross-trial ordering constraints and fixed repetition schedules, so built-in label-level generation is not sufficient.
  - The generated trial data passed into `run_trial.py` is a per-trial dictionary with `condition_id`, `block_kind`, `block_num`, `pair_id`, `left_symbol`, `right_symbol`, `correct_key`, `correct_symbol`, and timing fields.
- Runtime-generated trial values:
  - Left/right symbol placement is generated from a deterministic seed derived from `overall_seed`, block index, and trial index.
  - Block repetition is decided at runtime from observed pair accuracies.
  - If a training block fails criterion, the same block plan is replayed deterministically.

### Trial State Machine

1. State name: `instruction`
   - Onset trigger: experiment onset
   - Stimuli shown: task instructions, five symbols preview, key mapping
   - Valid keys: continue key
   - Timeout behavior: wait indefinitely for continue
   - Next state: `block_intro`
2. State name: `block_intro`
   - Onset trigger: block onset
   - Stimuli shown: block-specific instructions and trial count
   - Valid keys: continue key
   - Timeout behavior: wait indefinitely for continue
   - Next state: `training_fixation` or `test_fixation`
3. State name: `training_fixation`
   - Onset trigger: trial fixation onset
   - Stimuli shown: fixation cross
   - Valid keys: none
   - Timeout behavior: fixed-duration presentation
   - Next state: `training_pair_display`
4. State name: `training_pair_display`
   - Onset trigger: pair onset
   - Stimuli shown: two Hiragana symbols, left and right
   - Valid keys: left key `z`, right key `m`
   - Timeout behavior: response window expires after 3 s human / shorter QA-sim window in mode configs
   - Next state: `training_feedback`
5. State name: `training_feedback`
   - Onset trigger: feedback onset
   - Stimuli shown: `Correct`, `Incorrect`, or `Too slow`
   - Valid keys: none
   - Timeout behavior: fixed-duration presentation
   - Next state: `training_iti`
6. State name: `training_iti`
   - Onset trigger: ITI onset
   - Stimuli shown: fixation cross
   - Valid keys: none
   - Timeout behavior: fixed-duration presentation
   - Next state: next trial or block summary
7. State name: `test_fixation`
   - Onset trigger: trial fixation onset
   - Stimuli shown: fixation cross
   - Valid keys: none
   - Timeout behavior: fixed-duration presentation
   - Next state: `test_pair_display`
8. State name: `test_pair_display`
   - Onset trigger: pair onset
   - Stimuli shown: two Hiragana symbols, left and right
   - Valid keys: left key `z`, right key `m`
   - Timeout behavior: response window expires after 3 s human / shorter QA-sim window in mode configs
   - Next state: `test_iti`
9. State name: `test_iti`
   - Onset trigger: ITI onset
   - Stimuli shown: fixation cross
   - Valid keys: none
   - Timeout behavior: fixed-duration presentation
   - Next state: next trial or block summary
10. State name: `block_summary`
   - Onset trigger: block-end / repeat-decision moment
   - Stimuli shown: pair-wise accuracy summary and repeat/advance notice
   - Valid keys: continue key
   - Timeout behavior: wait indefinitely for continue
   - Next state: repeat same training block or advance
11. State name: `good_bye`
   - Onset trigger: goodbye onset
   - Stimuli shown: closing message
   - Valid keys: continue key
   - Timeout behavior: wait indefinitely for continue
   - Next state: end

## 3. Condition Semantics

- Condition ID: `training_premise`
  - Participant-facing meaning: learn the ordered premise pairs through feedback
  - Concrete stimulus realization (visual/audio): one of the premise pairs `ろ/ま`, `ま/か`, `か/め`, or `め/せ` with left/right order randomized; feedback text after response
  - Outcome rules: choose the symbol that is earlier in the learned order
- Condition ID: `test_premise`
  - Participant-facing meaning: recall the learned premise pairs without feedback
  - Concrete stimulus realization (visual/audio): same premise pairs as training, no feedback
  - Outcome rules: choose the symbol earlier in the learned order
- Condition ID: `test_transitive`
  - Participant-facing meaning: infer the novel transitive pair
  - Concrete stimulus realization (visual/audio): `ま/め` (BD) with left/right order randomized
  - Outcome rules: choose the symbol earlier in the learned hierarchy
- Condition ID: `test_anchor`
  - Participant-facing meaning: respond to the end-anchor control pair
  - Concrete stimulus realization (visual/audio): `ろ/せ` (AE) with left/right order randomized
  - Outcome rules: choose the symbol earlier in the learned hierarchy

Also document where participant-facing condition text/stimuli are defined:

- Participant-facing text source (config stimuli / code formatting / generated assets): config-defined text stimuli for instructions, prompts, feedback, and block summaries; symbol glyphs are text stimuli rendered in a Japanese-capable font
- Why this source is appropriate for auditability: all participant text and symbol rendering parameters stay in YAML, while `run_trial.py` only orchestrates state transitions and populates trial-specific symbol values
- Localization strategy (how language variants are swapped via config without code edits): instruction and prompt wording remain in config; only the font and text strings change per language profile, while the runtime uses the same state machine

## 4. Response and Scoring Rules

- Response mapping:
  - `z` selects the left symbol
  - `m` selects the right symbol
- Response key source (config field vs code constant):
  - Config-driven via `task.left_key` and `task.right_key`
- If code-defined, why config-driven mapping is not sufficient:
  - Not applicable; the mapping is config-driven
- Missing-response policy:
  - A missing response within the response window counts as a timeout
  - Training timeout shows `Too slow`
  - Test timeout is logged and advances without feedback
- Correctness logic:
  - For premise pairs, the symbol earlier in the fixed chain is correct
  - For BD, the correct response is `ま` because it precedes `め`
  - For AE, the correct response is `ろ` because it precedes `せ`
- Reward/penalty updates:
  - Correct training responses show `Correct`
  - Incorrect training responses show `Incorrect`
  - Timeouts show `Too slow`
- Running metrics:
  - Training-block accuracy by premise pair
  - Final test accuracy by condition
  - Mean correct RT
  - Timeout count

## 5. Stimulus Layout Plan

- Screen name: `instruction`
  - Stimulus IDs shown together: `instruction_text`
  - Layout anchors (`pos`): centered text block with the symbol preview placed beneath the main paragraph
  - Size/spacing (`height`, width, wrap): instruction text wraps to ~1000 px; symbol preview uses larger glyph height
  - Readability/overlap checks: keep the symbol preview separated from the paragraph by vertical spacing
  - Rationale: the participant needs the key mapping and the fact that there are five symbols, without exposing the learned order
- Screen name: `trial_pair`
  - Stimulus IDs shown together: `pair_left_symbol`, `pair_right_symbol`, `pair_prompt_text`
  - Layout anchors (`pos`): left symbol at approximately `[-220, 0]`, right symbol at `[220, 0]`, prompt below at `[0, -230]`
  - Size/spacing (`height`, width, wrap): large symbol glyphs for discrimination; prompt text smaller; no overlap with the pair
  - Readability/overlap checks: pair symbols must remain legible on a 1280x720 window and should not clip at the edges
  - Rationale: this is the core discrimination screen and must minimize crowding
- Screen name: `feedback`
  - Stimulus IDs shown together: `training_feedback_correct`, `training_feedback_incorrect`, `training_feedback_timeout`
  - Layout anchors (`pos`): centered
  - Size/spacing (`height`, width, wrap): short centered text, no extra elements
  - Readability/overlap checks: single-line or two-line centered layout only
  - Rationale: feedback should be immediately readable and visually distinct
- Screen name: `block_summary`
  - Stimulus IDs shown together: `block_summary_text`
  - Layout anchors (`pos`): centered
  - Size/spacing (`height`, width, wrap): medium text with generous wrap width
  - Readability/overlap checks: summary text must stay within the central viewport
  - Rationale: summarize criterion status before repeating or advancing

## 6. Trigger Plan

- `exp_onset`: experiment start
- `instruction_onset`: instruction screen
- `block_onset`: each training/test block start
- `trial_fixation_onset`: fixation before each pair
- `pair_onset`: pair display and response window start
- `response_z`: left-key response
- `response_m`: right-key response
- `trial_timeout`: no response before deadline
- `feedback_onset`: training feedback screen
- `block_end`: block completion and summary
- `good_bye_onset`: closing screen

## 7. Architecture Decisions (Auditability)

- `main.py` runtime flow style (simple single flow / helper-heavy / why): simple single flow with a small text-screen helper; block repetition logic stays readable in the main loop
- `utils.py` used? yes
- If yes, exact purpose (adaptive controller / sequence generation / asset pool / other): deterministic trial-sequence generation, pair orientation randomization, and block-accuracy summarization
- Custom controller used? yes
- If yes, why PsyFlow-native path is insufficient: the training protocol requires fixed block schedules and a repeat-until-criterion rule that cannot be expressed as a simple label sampler
- Legacy/backward-compatibility fallback logic required? no
- If yes, scope and removal plan: not applicable

## 8. Inference Log

- Decision: use the classic uninformed training protocol as the baseline task
  - Why inference was required: the source paper contains informed and uninformed variants, but the task repository needs one executable default
  - Citation-supported rationale: the uninformed version is the standard trial-by-trial learning protocol and preserves the core transitive-inference structure
- Decision: omit the post-experimental awareness questionnaire from the baseline runtime
  - Why inference was required: the questionnaire is a secondary measurement module rather than the core task flow
  - Citation-supported rationale: the paper treats awareness as an after-test assessment; the learning/test workflow is the task itself
- Decision: use a fixed feedback duration and ITI in the runtime implementation
  - Why inference was required: the methods specify the response window and feedback content, but not an exact on-screen duration for every auxiliary screen in the executable task
  - Citation-supported rationale: a short feedback interval and brief ITI are standard for this protocol family
- Decision: cap training block repeats with a small finite limit
  - Why inference was required: the paper specifies a repeat-until-criterion rule but not an upper bound
  - Citation-supported rationale: a finite retry cap prevents the task from stalling while still honoring the criterion

## Contract Note

- Participant-facing labels/instructions/options should be config-defined whenever possible.
- `src/run_trial.py` should not hardcode participant-facing text that would require code edits for localization.
