# Task Plot Brief

- Task: Transitive Inference Task
- Figure title: Transitive Inference Task
- Subtitle: Construct: inferential reasoning over learned hierarchy
- Source priority: `README.md`, `config/config.yaml`, `src/run_trial.py`, `references/task_logic_audit.md`.

## Timeline Rows

1. Training premise pairs
2. Final test premise pairs
3. Final test probes

## Trial Flow

Training trial:

1. Fixation, 400 ms.
2. Pair display, 3000 ms: two symbols shown left and right.
3. Participant presses `Z` for the left symbol or `M` for the right symbol.
4. Training feedback, 800 ms: Correct / Incorrect / Too slow.
5. ITI, 400 ms.

Final test trial:

1. Fixation, 400 ms.
2. Pair display, 3000 ms: two symbols shown left and right.
3. Participant presses `Z` for the left symbol or `M` for the right symbol.
4. No feedback.
5. ITI, 400 ms.

## Conditions

- Training premise pairs: AB, BC, CD, DE.
- Final test premise pairs: AB, BC, CD, DE.
- Final test probes: BD transitive probe and AE anchor probe.
- Training blocks repeat until every premise pair reaches 80% accuracy or the repeat limit is reached.
