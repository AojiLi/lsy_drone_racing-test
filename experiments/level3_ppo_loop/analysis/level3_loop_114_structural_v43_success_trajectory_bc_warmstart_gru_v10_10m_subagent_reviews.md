# Loop114 V43 Subagent Reviews

Trial:
`level3_loop_114_structural_v43_success_trajectory_bc_warmstart_gru_v10_10m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_114_structural_v43_success_trajectory_bc_warmstart_gru_v10_10m_analysis.md`

## Evaluator Metrics

Finding: reject v43 as executed; do not mature loop114 checkpoints.

Best checkpoint by analyzer score:

```text
lsy_drone_racing/control/checkpoints/level3_loop_114_structural_v43_success_trajectory_bc_warmstart_gru_v10_10m/level3_loop_114_structural_v43_success_trajectory_bc_warmstart_gru_v10_10m_step_005000000.ckpt
```

Metrics:

- success: `0/100`;
- mean gates: `0.01`;
- crash rate: `51%`;
- timeout rate: `49%`;
- failures by target gate: `99%` gate 0, `1%` gate 1.

The highest gate-progress milestone was 9M, but it still had `0%` success,
only `0.06` mean gates, and a worse `71%` crash rate.

Compared with the BC-only diagnostic, PPO did not improve: BC-only had `0%`
success but `0.15` mean gates, while loop114 peaked at `0.06` mean gates.
Compared with the global frontier, loop114 is far below loop107's `21%`
success and `1.66` mean gates.

## W&B / PPO Diagnostics

Finding: PPO erased the useful part of the BC warmstart signal. This is an
imitation-to-PPO handoff failure, not a train-longer signal.

Evidence:

- `approx_kl` fell from about `0.00238` to `0.00014`, and final summary was
  near zero;
- `clipfrac` went to `0`;
- entropy rose from about `2.28` to `2.33`, so the policy became more diffuse;
- policy loss stayed tiny;
- explained variance stayed essentially `0`, while value loss remained large;
- active teacher retention was off:
  `teacher_kl=0`, `teacher_action_mse=0`, `retention/sampled_batch_size=0`,
  and `v27_teacher_kl_beta=0`.

Race curves showed local shaping movement without task conversion:
`passed_gate_rate` stayed near `0.0002-0.0003`, `finished_rate=0`, and
evaluator mean gates fell below the BC-only baseline.

## Structure / Research Synthesis

Finding: reject v43 as executed. The likely failure is training structure and
retention, not track geometry, deployment path, or obvious GRU/v10 wiring.

The evidence chain is:

- v41 cleared GRU/v10 wiring;
- v43 preflight showed the GRU/v10 student can imitate teacher actions;
- loop114 had no active retention during PPO;
- PPO fine-tuning erased the small BC first-gate signal.

Recommended next named lane:

```text
v44_sequence_success_retention_failure_correction_gru_v10
```

Hypothesis: one-shot BC warmstart is too fragile. PPO needs active
sequence-level retention/rehearsal of successful train-pool behavior, plus
broader train-pool failure-correction coverage, while deployment remains a
single PPO Actor.

Required boundaries:

- train and hard eval on unchanged `config/level3.toml`;
- no Level3 geometry/randomization edits;
- no MPC, planner, fallback, shield, or teacher at inference;
- deployment remains `observation/history -> PPO Actor -> roll/pitch/yaw/thrust`.

Recommended preflight before v44 training:

- build a larger disjoint train-pool success dataset;
- implement or verify recurrent retention sampled during PPO with nonzero
  batch size and finite KL/MSE/agreement;
- audit episode-level sequence retention;
- run bounded hard-eval milestones.

If active retention still falls below the BC-only `0.15` mean-gates diagnostic
and remains below `0.5` mean gates, retire the v10 true-GRU imitation path and
re-anchor on the v5 frontier.
