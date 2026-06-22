# Evaluator Metrics Review: loop090 v29 Success-Churn Replay

Scope: hard eval on unchanged `config/level3_dr.toml`, `validation_unseen`
only. No `final_locked` seeds were used.

## Key Finding

The best loop090 checkpoint is 3M:

`lsy_drone_racing/control/checkpoints/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m_step_003000000.ckpt`

Metrics:

- success: 14 / 100
- success rate: 0.14
- crash rate: 0.86
- timeout rate: 0.00
- mean gates: 1.39
- mean successful time: 6.72s

The successful runs are fast enough, but success is far below the 0.60 target.
The target is not met.

## Comparison

| Run | Best validation checkpoint | Success | Crash | Mean Gates | Mean Successful Time |
| --- | --- | ---: | ---: | ---: | ---: |
| loop052 anchor | final | 0.20 | 0.80 | 1.47 | 6.858s |
| loop088 | 4M | 0.19 | 0.81 | 1.57 | 6.846s |
| loop089 | 2M | 0.18 | 0.82 | 1.49 | 7.002s |
| loop090 | 3M | 0.14 | 0.86 | 1.39 | 6.720s |

Loop090 is slightly faster among successes, but loses success rate, crash rate,
and gate progress.

## Milestone Pattern

Loop090 improved only weakly from 2M to 3M: success moved from 0.12 to 0.14,
and mean gates moved from 1.32 to 1.39. This remains below loop052, loop088,
and loop089. There is no evaluator evidence to mature this v29 branch.

## Failure Taxonomy

Failures remain crash-dominated. At the best checkpoint all 86 failures are
`bounds_or_ground`; there are no timeouts.

Failures by target gate:

- gate 0: 35
- gate 1: 22
- gate 2: 26
- gate 3: 3

This is still primarily early/mid-course loss, not a finish-speed problem.

## Recommendation

Evaluator metrics support `hold_for_more_analysis`.

Do not continue or mature loop090/v29 on evaluator evidence alone, and do not
accept the checkpoint. Any next run needs a main-agent decision packet with
non-evaluator evidence for a named structural lane or explicit reward/training
number change.
