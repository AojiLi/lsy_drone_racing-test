# Loop081 V25 Minimal Aperture Ablation Synthesis

Scope: local synthesis after rejecting loop081/v24. This does not modify
`config/level3_dr.toml`; hard acceptance remains success rate `>= 0.60` and
mean successful time `<= 7.0s` on unchanged `config/level3_dr.toml`.

Inputs:

- Loop081 analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m_analysis.md`
- Loop081 hard-eval summary:
  `experiments/level3_ppo_loop/level3_loop_081_structural_v24_v22_hybrid_aperture_corridor_obs_from_loop078_final_20m_eval_summary.csv`
- Previous v24 decision:
  `experiments/level3_ppo_loop/decisions/2026-06-22_loop080_reject_v23_launch_v24_hybrid_aperture_corridor_obs.md`
- Existing v8 frontier:
  `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`
- Rejected v10 hybrid layout:
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`

## Summary

Loop081/v24 is rejected. It appended the full v9 aperture-margin block to the
v8 gate-corridor observation, but it did not preserve the loop078 frontier.
Compared with loop078 final, v24 regressed from 0.25 to 0.15 success, from 2.05
to 1.45 mean gates, and from 0.75 to 0.85 crash rate.

The likely issue is not PPO instability. W&B/PPO diagnostics showed low KL,
low clip fraction, stable entropy, and acceptable explained variance. The
failure mode is non-conversion: training reward improved, but gate passing and
finish signals stayed flat.

## Hypothesis

`v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m`

The v10 layout may have introduced redundant inputs because v8 already includes
`target_progress` and current gate-frame position through its phase-progress
block. V25 keeps v8 intact and appends only the five square-aperture margin
features:

- left margin
- right margin
- bottom margin
- top margin
- radial aperture margin

This isolates whether aperture clearance helps without duplicating existing
gate-frame position features.

## Contract

- initial checkpoint: loop078 final
- train config: `level3_dr.toml`
- hard eval config: unchanged `level3_dr.toml`
- observation layout:
  `level3_gate_corridor_aperture_margin_minimal_2obs_local_history_v11`
- policy: 2x256 Tanh MLP
- reward structure: `legacy_staged`
- reward/PPO/controller numbers: loop078/v22 defaults
- training horizon: 20M with 5M checkpoint evaluation
- warm-start: zero-pad only the newly appended five input weights

## Rollback

Reject or hold if no milestone preserves loop078 retention:

- success below 0.25
- mean gates below 2.05
- crash above 0.75

Promote only if it creates a hard-eval frontier on unchanged
`config/level3_dr.toml`.
