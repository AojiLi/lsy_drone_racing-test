# Loop079 V22 Maturation Regression Synthesis

Scope: diagnostic synthesis after rejecting loop079/v22 maturation. This does
not train, tune, or modify `config/level3_dr.toml`. Hard acceptance remains
success rate `>= 0.60` and mean successful time `<= 7.0s` on unchanged
`config/level3_dr.toml`.

Inputs:

- Loop079 analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_079_structural_v22_gate_corridor_obs_mature_loop078_final_to_60m_analysis.md`
- Loop079 hold decision:
  `experiments/level3_ppo_loop/decisions/2026-06-22_loop079_reject_v22_maturation_hold_for_trace_diagnostics.md`
- Trace diagnostic report:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop078_079_v22_maturation_regression_trace_diagnostic_report.md`
- Trace diagnostic episodes:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop078_079_v22_maturation_regression_trace_diagnostic_episodes.csv`
- Weight-interpolation evaluation:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop080_v22_weight_interpolation_eval_summary.csv`

## Summary

Loop079 rejected same-hypothesis v22 maturation. The branch did not mature into
better hard-eval behavior; it lost success retention from the loop078 global
best.

| Checkpoint | Success | Success Seeds | Mean Gates | Crash | Mean Success Time |
| --- | ---: | --- | ---: | ---: | ---: |
| loop078 final | 0.25 | 4, 9, 12, 18, 19 | 2.05 | 0.75 | 8.048 |
| loop079 20M | 0.10 | 4, 18 | 1.55 | 0.90 | 8.300 |
| loop079 25M | 0.05 | 9 | 1.05 | 0.95 | 6.860 |
| loop079 30M | 0.15 | 4, 9, 16 | 1.55 | 0.85 | 7.007 |
| loop079 35M | 0.10 | 9, 18 | 1.15 | 0.90 | 8.910 |
| loop079 final | 0.15 | 1, 4, 9 | 1.35 | 0.85 | 7.993 |

The fixed-seed union across loop078 and loop079 contains complementary
successes `[1, 4, 9, 12, 16, 18, 19]`, but no single checkpoint preserves them.
Simple training continuation therefore behaves like behavioral drift/forgetting,
not monotonic skill acquisition.

## Failure Pattern

- Loop079 failed the loop078 rollback gates: success `< 0.20`, mean gates
  `< 2.00`, and crash `> 0.80`.
- The best loop079 speed milestone was 30M, but it traded away success/gates.
- Dominant endpoint classes stayed near-gate obstacle and gate-frame crashes.
- PPO/W&B diagnostics did not show a collapse: KL/clip/explained-variance
  looked stable enough that this is not a direct optimizer-divergence diagnosis.
- The evaluation-only weight interpolation test did not recover the union:
  the best interpolation reached only 0.20 success and 2.00 mean gates, below
  loop078's 0.25 success and 2.05 mean gates.

## Rejected Directions

Do not continue unchanged:

- v22 maturation from loop078 at learning rate `5e-5`
- simple checkpoint interpolation/averaging between loop078 and loop079
- another automatic strong gate-reward increase like v21

Do not treat W&B train reward improvement as sufficient evidence. The hard
evaluator is the acceptance gate.

## Next Candidate Direction

The next useful lane should start from the loop078 global best, preserve the v8
gate-corridor observation, and directly target retention plus near-gate
obstacle/frame crashes.

Recommended lane:

`v23_v22_frame_obstacle_retention_from_loop078_final_20m`

Contract:

- initial checkpoint: loop078 final
- train config: `level3_dr.toml`
- hard eval config: unchanged `level3_dr.toml`
- observation: `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`
- policy: 2x256 Tanh MLP
- training horizon: 20M with 5M checkpoint evaluation
- lower learning rate from `5e-5` to `2e-5` to reduce retention loss
- keep constant LR (`anneal_lr=false`)
- switch reward structure from `legacy_staged` to
  `decoupled_frame_clearance` so frame pressure is an active term
- add modest frame pressure `gate_frame_pressure_coef=1.0`
- increase obstacle safety from `obstacle_coef=8.0`, `obstacle_margin=0.4` to
  `obstacle_coef=10.0`, `obstacle_margin=0.45`
- reduce time pressure from `time_penalty=0.03` to `0.015`
- keep gate-stage, gate-axis, gate bonus, finish bonus, controller action
  limits, and observation layout unchanged

Promotion rule:

- promote if a milestone beats loop078 on success (`> 0.25`), or
- keeps success `>= 0.25` while reducing crash below `0.75`, or
- keeps success `>= 0.25` and mean gates `>= 2.05` while moving mean
  successful time toward `<= 7.0s`

Reject or hold if it falls below 0.20 success, mean gates below 2.00, or crash
above 0.80 without a compensating new success frontier.
