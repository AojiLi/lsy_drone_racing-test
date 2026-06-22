# Loop082 V26 V23-10M Success Replay Retention Synthesis

Scope: local synthesis after rejecting loop082/v25 and completing post-hold
trace diagnostics. This does not modify `config/level3_dr.toml`; hard
acceptance remains success rate `>= 0.60` and mean successful time `<= 7.0s`
on unchanged `config/level3_dr.toml`.

## Inputs

- Loop082 decision:
  `experiments/level3_ppo_loop/decisions/2026-06-22_loop082_reject_v25_hold_for_trace_diagnostics.md`
- Loop082 analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m_analysis.md`
- Post-hold synthesis:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_post_hold_trace_and_interpolation_synthesis.md`
- Loop078/v24/v25 trace diagnostic:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_v25_vs_loop078_v24_trace_diagnostic_report.md`
- Loop078/v23-10M trace diagnostic:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop082_loop078_vs_v23_10m_trace_diagnostic_report.md`
- Loop078/v23-10M interpolation eval:
  `experiments/level3_ppo_loop/diagnostics/2026-06-22_loop083_loop078_v23_10m_weight_interpolation_eval_summary.csv`

## Evidence

The current global best is loop078 final:

- success: 0.25
- mean gates: 2.05
- crash: 0.75
- mean successful time: 8.048s
- successful seeds: 4, 9, 12, 18, 19

V23 10M is the closest post-loop078 variant:

- success: 0.20
- mean gates: 2.00
- crash: 0.80
- mean successful time: 8.855s
- successful seeds: 4, 5, 12, 18

V24 and v25 are rejected:

- v24 final: 0.15 success, 1.45 mean gates, 0.85 crash
- v25 best: 0.10 success, 1.35 mean gates, 0.90 crash

Simple interpolation between loop078 final and v23 10M did not improve the
frontier. The best interpolation was alpha 0.25 with 0.20 success, 2.00 mean
gates, and 0.80 crash.

## Hypothesis

`v26_v23_10m_success_replay_retention_20m`

Continue from v23 10M, not from v25 and not from a weight interpolation.
Use the same v8 gate-corridor obstacle observation and v23 decoupled
frame-clearance reward settings, but train with a low-probability hard-eval
success replay profile over the union of loop078 and v23-10M successful seeds:

- 4, 5, 9, 12, 18, 19

The goal is to preserve v23's retained seeds 4/12/18 and gained seed 5 while
reintroducing loop078's lost seeds 9/19. The replay probability is deliberately
low so the policy still trains primarily on the default randomized Level3
distribution.

## Contract

- initial checkpoint: v23 10M
- train config: `level3_dr.toml`
- hard eval config: unchanged `level3_dr.toml`
- observation layout: `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`
- policy: 2x256 Tanh MLP
- reward structure: `decoupled_frame_clearance`
- reward/PPO/controller numbers: v23 settings
- training-only track generator profile:
  `loop078_v23_success_replay_lowprob`
- training horizon: 20M with 5M checkpoint evaluation
- W&B project: `ADR-PPO-Racing-Level3`

## Promotion And Rollback

Promote or mature if a milestone reaches one of:

- success `> 0.25`
- success `>= 0.25` and mean gates `>= 2.05`
- success `>= 0.25` and crash `< 0.75`
- clear seed-retention improvement over both loop078 and v23 10M

Reject or hold if no milestone preserves the loop078 frontier:

- success below 0.25
- mean gates below 2.05
- crash above 0.75

Do not modify Level3 track geometry, randomization in `config/level3_dr.toml`,
gates, or obstacles.
