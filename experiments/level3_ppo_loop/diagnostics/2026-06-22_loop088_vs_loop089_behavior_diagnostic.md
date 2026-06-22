# Loop088 vs Loop089 Behavior Diagnostic

Status: diagnostic only. This packet does not approve a new training chunk.

## Scope

Compared validation-unseen episodes only:

- loop088 4M: `level3_loop_088_structural_v28_success24_retention_bounds_replay_5m_step_004000000.ckpt`
- loop089 2M: `level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m_step_002000000.ckpt`

No `final_locked` seeds were used.

## Headline

Loop089's stronger gate reward numbers did not create a better gate-conversion policy. It lost one net validation success, reduced mean gates, and increased `bounds_or_ground` failures.

| Metric | Loop088 4M | Loop089 2M | Delta |
| --- | ---: | ---: | ---: |
| success seeds | 19 | 18 | -1 |
| bounds_or_ground endpoints | 81 | 82 | +1 |
| mean gates per seed | 1.570 | 1.490 | -0.080 |
| mean cmd tilt over-limit frac | 0.283 | 0.266 | -0.016 |
| mean target gate frame distance | 1.477 | 1.512 | +0.035 |

## Success Churn

- kept successes: 12 seeds: 112, 123, 134, 152, 155, 161, 167, 175, 182, 184, 185, 194
- lost loop088 successes: 7 seeds: 107, 109, 125, 149, 153, 169, 192
- gained loop089 successes: 6 seeds: 120, 121, 136, 160, 163, 187
- loop052 anchor successes kept by loop088: 11
- loop052 anchor successes kept by loop089: 15

### Lost Success Seeds

| seed | gates_088 | gates_089 | delta_gates | target_gate_089 | endpoint_089 | time_s_088 | time_s_089 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 107 | 4 | 0 | -4 | 0 | bounds_or_ground | 7.160 | 1.160 |
| 109 | 4 | 2 | -2 | 2 | bounds_or_ground | 9.880 | 5.920 |
| 125 | 4 | 2 | -2 | 2 | bounds_or_ground | 7.060 | 4.840 |
| 149 | 4 | 2 | -2 | 2 | bounds_or_ground | 6.460 | 3.560 |
| 153 | 4 | 2 | -2 | 2 | bounds_or_ground | 4.500 | 3.020 |
| 169 | 4 | 0 | -4 | 0 | bounds_or_ground | 7.620 | 1.180 |
| 192 | 4 | 2 | -2 | 2 | bounds_or_ground | 6.320 | 4.460 |

### Gained Success Seeds

| seed | gates_088 | gates_089 | delta_gates | target_gate_088 | endpoint_088 | time_s_088 | time_s_089 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 120 | 2 | 4 | 2 | 2 | bounds_or_ground | 4.440 | 8.800 |
| 121 | 1 | 4 | 3 | 1 | bounds_or_ground | 1.580 | 8.340 |
| 136 | 2 | 4 | 2 | 2 | bounds_or_ground | 4.340 | 6.120 |
| 160 | 1 | 4 | 3 | 1 | bounds_or_ground | 1.800 | 6.780 |
| 163 | 0 | 4 | 4 | 0 | bounds_or_ground | 1.360 | 6.500 |
| 187 | 1 | 4 | 3 | 1 | bounds_or_ground | 2.240 | 6.860 |

## Gate Progress Movement

- seeds with fewer gates after loop089: 18
- seeds with more gates after loop089: 12
- regressed seeds by loop089 target gate: {0: 5, 1: 7, 2: 6}
- improved seeds by loop089 target gate: {1: 2, 2: 3, 3: 7}

Failure by target gate moved from:

- loop088: {0: 33, 1: 20, 2: 23, 3: 5}
- loop089: {0: 34, 1: 22, 2: 23, 3: 3}

The adjustment increased target-gate failure pressure at gate0 and gate1 while reducing gate3 failures. That is consistent with the evaluator finding: more early/mid gate-conversion trouble, not a late-race speed problem.

## Interpretation

The loop089 reward adjustment improved W&B reward and strengthened retention metrics, but the episode-level hard eval shows a behavioral regression:

- net success decreased;
- `bounds_or_ground` endpoints increased;
- mean gates decreased;
- loop089 lost 7 loop088 successes and gained only 6 different successes;
- the failures remained concentrated at gate0/gate1/gate2.

This supports rejecting the gate reward escalation. It does not prove the v28 data-correction idea is useless; it shows that simply increasing gate-stage/axis/pass bonuses from loop088 4M is not the right conversion mechanism.

## Next Hypothesis Candidate

Do not launch training from this packet alone.

A future packet should consider a named lane that reverts the loop089 reward escalation and changes the data/behavior path instead, for example:

`v29_revert_reward_success_churn_retention_replay`

Candidate constraints:

- start from loop088 4M, not loop089;
- revert reward numbers to loop088/v28 values;
- keep success24 teacher retention and v8 observation;
- focus on preserving loop088 successes while correcting specific lost-success/failure seeds through train-pool behavior diagnostics;
- keep hard eval on unchanged `config/level3_dr.toml`;
- do not use `final_locked` seeds.

Artifacts:

- JSON: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop088_vs_loop089_behavior_diagnostic.json`
- Seed delta CSV: `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop088_vs_loop089_seed_delta.csv`
