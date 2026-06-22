# Loop075 Trace Diagnostic Synthesis

Scope: diagnostic-only synthesis after loop075. This does not modify
`config/level3_dr.toml`; hard acceptance remains success rate `>= 0.60` and
mean successful time `<= 7.0s` on the unchanged Level3 hard evaluator.

Inputs:

- Loop075 analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_075_structural_v19_lowprob_replay_success_retention_mature_loop074_20m_to_60m_analysis.md`
- Loop075 hold decision:
  `experiments/level3_ppo_loop/decisions/2026-06-22_loop075_reject_v19_maturation_hold_for_trace_diagnostics.md`
- Trace report:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop069_071_074_075_v19_trace_diagnostic_report.md`
- Trace episodes CSV:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop069_071_074_075_v19_trace_diagnostic_episodes.csv`

## Replay Vs Non-Replay Finding

Replay seed set used for the v19 diagnostic:

`[1, 4, 9, 11, 12, 16, 17, 18, 20]`

| Checkpoint | All Success | All Gates | Replay Success | Replay Gates | Non-Replay Success | Non-Replay Gates |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| loop069 25M | 0.10 | 1.45 | 0.222 | 2.00 | 0.000 | 1.00 |
| loop071 20M | 0.25 | 2.00 | 0.333 | 2.44 | 0.182 | 1.64 |
| loop074 20M | 0.20 | 1.60 | 0.444 | 2.67 | 0.000 | 0.73 |
| loop075 25M | 0.15 | 1.55 | 0.333 | 2.22 | 0.000 | 1.00 |
| loop075 30M | 0.10 | 1.70 | 0.222 | 2.22 | 0.000 | 1.27 |

Loop071 is the only checkpoint in this comparison that succeeds on non-replay
seeds. The later seed-replay family improves or retains replay-seed success
but loses default-distribution transfer.

## Failure Pattern

- v19/loop074 restored some replay-seed success, but all successes were on
  replay seeds.
- v19 maturation/loop075 failed both promotion and rollback: success fell to
  0.15 at the best milestone and 0.10 at the 30M mean-gates blip.
- Non-replay success was 0/11 for loop074 20M, loop075 25M, and loop075 30M.
- The non-replay endpoint classes remain dominated by obstacle and frame
  crashes, especially `near_gate_obstacle`, `pre_plane_obstacle`, and
  `gate_vertical_frame`.
- PPO diagnostics from loop075 were stable enough that this is not primarily
  an optimizer instability signal.

## Decision Implication

Reject the seed-replay family for the next chunk. More replay probability
tuning is not justified by the diagnostic because replay success improved at
the cost of non-replay transfer.

The next useful test is a narrow default-distribution recovery screen from the
only frontier checkpoint with non-replay successes:

- initial checkpoint: loop071 20M
- train config: `level3_dr.toml`
- hard eval config: `level3_dr.toml`
- track generator profile: `default`
- observation: v5 local-obstacle
- policy: 2x256 Tanh MLP
- reward/PPO/controller numbers: unchanged from the loop071/v17 family
- horizon: 20M with 5M checkpoint evals

This tests whether loop071's non-replay transfer can be preserved or improved
without hard-corridor or seed-replay bias. If it fails to beat loop071's
success/gates frontier or at least the loop069 global-best rollback floor, the
next stage should hold for a broader structural review rather than adding more
seed replay.
