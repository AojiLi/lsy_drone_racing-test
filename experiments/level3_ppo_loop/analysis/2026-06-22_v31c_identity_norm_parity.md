# v31c Identity-Norm Warm-Start Parity

Status: passed.

## Scope

This parity check evaluates the identity-normalized loop094 4M warm-start
checkpoint before any v31c training.

Track boundary:

- config: `config/level3.toml`
- seed split: `validation_unseen`
- seeds: 101-200
- inference module: `ppo_level3_inference`
- no Level3 track geometry/randomization changes

## Checkpoints

Source checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m/level3_loop_094_structural_v31a_longer_rollout_clean_ppo_5m_step_004000000.ckpt`

Identity-normalized checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_094_v31a_4m_identity_norm_warmstart/level3_loop_094_v31a_4m_identity_norm_warmstart.ckpt`

The identity checkpoint adds actor observation normalization metadata with
`mean=0`, `var=1`, and identity return-normalization metadata. It does not
change model weights.

## Result

The identity-normalized checkpoint matches loop094 4M hard-eval behavior:

- success: `19/100`
- success rate: `0.19`
- mean successful time: `6.875789473684211s`
- crash rate: `0.81`
- timeout rate: `0.0`
- mean gates: `1.55`
- success seeds:
  `[110, 121, 123, 124, 134, 136, 142, 152, 154, 155, 160, 161, 167, 169, 175, 184, 185, 187, 192]`

## Decision

The zero-update parity gate required by
`experiments/level3_ppo_loop/decisions/2026-06-22_loop095_reject_v31b_launch_v31c_identity_norm_warmstart.md`
is satisfied.

v31c may proceed to the approved 5M screen with 1M milestone hard evals.
