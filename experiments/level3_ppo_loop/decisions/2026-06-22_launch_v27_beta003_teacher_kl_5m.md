# Launch V27 Beta0.03 Teacher KL Screen

Decision: launch_named_structural_lane

## Scope

Launch only this named structural lane after the v27 teacher-retention KL
implementation passes sanity checks:

`v27_teacher_retention_beta003_5m`

This is the light nonzero-beta teacher-retention screen. It follows the
loop085 beta=0 negative control and tests whether real teacher retention
prevents short-continuation behavior drift.

## Contract

- hard evaluation remains on unchanged `config/level3_dr.toml`;
- do not edit Level3 track geometry, gates, obstacles, randomization, or
  final_locked seeds;
- do not use final_locked seeds during automatic loop work;
- train config remains `level3_dr.toml`;
- student observation layout:
  `level3_gate_corridor_obstacle_relative_2obs_local_history_v8`;
- teacher observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`;
- policy: 2x256 Tanh MLP;
- student initial checkpoint: loop078 final;
- frozen teacher checkpoint: loop052 final;
- beta: `0.03`;
- training horizon: `5M`;
- checkpoint interval: `1M`;
- evaluator protocol: `dev_then_validation`, Wilson CI, failure taxonomy;
- W&B project: `ADR-PPO-Racing-Level3`.

## Implementation Gate

Do not launch the 5M screen unless all are true:

- retention dataset path exists;
- dataset excludes `dev_seen`, `validation_unseen`, and `final_locked` seeds;
- training dry-run includes a real `v27_retention_dataset_path`;
- a short sanity run logs nonzero `retention/sampled_batch_size`;
- `losses/teacher_kl` is finite;
- `retention/teacher_agreement` is finite.

## Stop Rule

After the 5M screen, run the analyzer and exactly three reviews before any next
training chunk.

Hold if:

- validation success remains below the loop052 anchor and mean gates do not
  improve;
- retention metrics are zero or NaN;
- W&B reward improves without hard-eval conversion;
- failure taxonomy shows stronger bounds/ground crash drift than loop052.
