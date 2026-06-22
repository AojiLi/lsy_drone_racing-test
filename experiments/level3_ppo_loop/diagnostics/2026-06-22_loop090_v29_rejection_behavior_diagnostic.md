# Loop090 v29 Rejection Behavior Diagnostic
Status: diagnostic and hold evidence. This packet does not approve another training chunk.
## Validation Summary
| Run | Success | Crash | Mean Gates | Mean Success Time | Success Seeds |
| --- | ---: | ---: | ---: | ---: | --- |
| loop052_anchor | 0.20 | 0.80 | 1.47 | 6.858s | [106, 112, 120, 123, 132, 134, 145, 152, 155, 160, 161, 163, 166, 167, 175, 182, 184, 185, 187, 199] |
| loop088_4M | 0.19 | 0.81 | 1.57 | 6.8463s | [107, 109, 112, 123, 125, 134, 149, 152, 153, 155, 161, 167, 169, 175, 182, 184, 185, 192, 194] |
| loop089_2M | 0.18 | 0.82 | 1.49 | 7.0022s | [112, 120, 121, 123, 134, 136, 152, 155, 160, 161, 163, 167, 175, 182, 184, 185, 187, 194] |
| loop090_3M | 0.14 | 0.86 | 1.39 | 6.72s | [109, 123, 149, 152, 155, 160, 161, 163, 167, 182, 184, 185, 187, 194] |

Loop090/v29 is worse than loop052, loop088, and loop089 on success, crash, and mean gates. Its only favorable metric is speed among the few successful episodes.

## Validation Success Churn

### loop088 4M -> loop090 3M
- kept successes: 11: [109, 123, 149, 152, 155, 161, 167, 182, 184, 185, 194]
- lost successes: 8: [107, 112, 125, 134, 153, 169, 175, 192]
- gained successes: 3: [160, 163, 187]

### loop089 2M -> loop090 3M
- kept successes: 12: [123, 152, 155, 160, 161, 163, 167, 182, 184, 185, 187, 194]
- lost successes: 6: [112, 120, 121, 134, 136, 175]
- gained successes: 2: [109, 149]

### loop052 anchor -> loop090 3M
- kept successes: 11: [123, 152, 155, 160, 161, 163, 167, 182, 184, 185, 187]
- lost successes: 9: [106, 112, 120, 132, 134, 145, 166, 175, 199]
- gained successes: 3: [109, 149, 194]

At loop090 best, all 86 validation failures are `bounds_or_ground`; failure target gates are {'0': 35, '1': 22, '2': 26, '3': 3}. This remains early/mid-course instability rather than a late-race speed problem.

## Train-Pool Replay Efficacy
| Run on train_pool_2300_2399 | Overall Success | Overall Crash | Mean Gates | Successes on 16 replay seeds |
| --- | ---: | ---: | ---: | ---: |
| loop088_4M | 0.10 | 0.90 | 1.38 | 10/16 |
| loop089_2M | 0.14 | 0.86 | 1.47 | 14/16 |
| loop090_3M | 0.12 | 0.88 | 1.41 | 7/16 |

The v29 sampler was built from the union of loop088 and loop089 train-pool success-churn seeds. On that exact 16-seed replay set, loop090 succeeds on only 7/16, compared with 10/16 for loop088 and 14/16 for loop089. This means the replay lane did not even preserve the behavior it was designed to retain on its source slice.

## Decision Implication

Reject v29 as a continuation lane. Do not continue it to 60M/90M, and do not launch another automatic reward-number tweak from this state. The next training step, if any, must be a fresh named structural/training hypothesis with a new decision packet.

## Artifacts
- JSON: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop090_v29_rejection_behavior_diagnostic.json`
- Validation churn matrix: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop090_validation_churn_matrix.csv`
- Train-pool replay seed matrix: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop090_train_pool_replay_seed_matrix.csv`
