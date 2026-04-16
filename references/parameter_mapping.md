# Parameter Mapping

## Mapping Table

| Parameter ID | Config Path | Implemented Value | Source Paper ID | Evidence (quote/figure/table) | Decision Type | Notes |
|---|---|---|---|---|---|---|
| chain_symbols | `task.chain_symbols` | `["ろ", "ま", "か", "め", "せ"]` | W2093778263 | Figure 1 shows the five Hiragana symbols in hierarchical order. | direct | Core ordered stimulus set. |
| premise_pairs | `task.premise_pairs` | `["AB", "BC", "CD", "DE"]` | W2093778263 | Methods describe adjacent pair training from the five-symbol hierarchy. | direct | Defines the learned order chain. |
| training_block_1_pattern | `task.training_block_patterns.block_1` | `ABx5, BCx5, CDx5, DEx5, repeated twice` | W2093778263 | Methods specify the first training block schedule. | direct | 40 trials. |
| training_block_2_pattern | `task.training_block_patterns.block_2` | `ABx2, BCx2, CDx2, DEx2, repeated five times` | W2093778263 | Methods specify the second training block schedule. | direct | 40 trials. |
| training_block_3_pattern | `task.training_block_patterns.block_3` | `AB, BC, CD, DE, repeated ten times` | W2093778263 | Methods specify the third training block schedule. | direct | 40 trials. |
| training_block_4_pattern | `task.training_block_patterns.block_4` | `random order, 10 presentations of each premise pair` | W2093778263 | Methods specify the final training block schedule. | direct | 40 trials. |
| test_block_pattern | `task.test_block_pattern` | `cycle_count: 1, randomize: true, pair_repeats: AB/BC/CD/DE/BD/AE each repeated 8 times` | W2093778263 | Methods specify premise, transitive, and anchor test pairs in the final test. | direct | 48-trial final test block. |
| accuracy_threshold | `task.training_accuracy_threshold` | `0.80` | W2093778263 | Methods require at least 80% accuracy on every premise pair before advancing. | direct | Training repetition criterion. |
| response_window_s | `task.response_window_s` | `3.0` | W2093778263 | Methods describe a 3 s response window for the pair judgment. | direct | QA/sim modes may shorten this value. |
| left_key | `task.left_key` | `z` | W2093778263 | Methods use Z/M response keys for left/right selection. | direct | Left choice. |
| right_key | `task.right_key` | `m` | W2093778263 | Methods use Z/M response keys for left/right selection. | direct | Right choice. |
| feedback_duration_s | `task.feedback_duration_s` | `0.8` | W2093778263 | The paper states feedback content but not a precise onscreen duration. | inferred | Short fixed feedback interval for runtime clarity. |
| iti_duration_s | `task.iti_duration_s` | `0.4` | W2093778263 | The paper does not specify the inter-trial interval duration. | inferred | Brief fixation ITI between trials. |
| block_repeat_limit | `task.block_repeat_limit` | `3` | W2093778263 | The paper uses a repeat-until-criterion rule but not a hard cap. | inferred | Prevents infinite repetition in the executable task. |
