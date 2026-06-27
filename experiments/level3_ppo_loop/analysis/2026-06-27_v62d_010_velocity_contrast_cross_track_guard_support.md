# v62d_010 Velocity-Contrast Cross-Track Guard Support

Date: 2026-06-27

## Purpose

Support the next candidate selected by:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_meta_review_launch_v62d_010.md
```

Candidate:

```text
v62d_010_velocity_contrast_cross_track_guard
```

The support task was to add a safe way to pass the generic clean tracker reward
override:

```text
trajectory_cross_track_coef=1.8
```

without allowing gate, aperture, obstacle, race, finish, or stage rewards into
the v60/v62 clean bottom-tracker lane.

## Code Support

Changed files:

```text
scripts/train_v60_brax_ppo_smoke.py
scripts/train_v62_brax_reference_command_tracker.py
scripts/audit_v62b_brax_ppo_signals.py
```

The new CLI option is:

```text
--reward-coeff NAME=VALUE
```

Allowed names are limited to clean command-tracker coefficients such as:

```text
trajectory_cross_track_coef
trajectory_along_speed_coef
trajectory_reverse_speed_coef
trajectory_overshoot_coef
semantic_brake_speed_coef
semantic_slow_speed_coef
semantic_slow_stop_coef
semantic_recover_speed_coef
```

Forbidden gate/obstacle/race coefficients such as `gate_cross_bonus` and
`obstacle_coef` are rejected by the parser.

## Checks

Compile check:

```text
pixi run -e gpu python -m py_compile \
  scripts/train_v60_brax_ppo_smoke.py \
  scripts/train_v62_brax_reference_command_tracker.py \
  scripts/audit_v62b_brax_ppo_signals.py
```

Result:

```text
passed
```

Parser check:

```text
trajectory_cross_track_coef=1.8 accepted
gate_cross_bonus rejected
```

Config check:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
```

## Support Smoke

Command:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_010_velocity_contrast_cross_track_guard_support \
  --config level3_tracker_free_space.toml \
  --seed 26500 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 262144 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --value-target-scale 1.0 \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile velocity_contrast_constant_speed \
  --reward-coeff trajectory_cross_track_coef=1.8 \
  --checkpoint-interval 262144 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_010_velocity_contrast_cross_track_guard_support/v62d_010_velocity_contrast_cross_track_guard_support_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_010_velocity_contrast_cross_track_guard_support_summary.json \
  --eval-rollouts 4 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_010_velocity_contrast_cross_track_guard_support \
  --wandb-run-id v62d_010_velocity_contrast_cross_track_guard_support_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_010_velocity_contrast_cross_track_guard_support_20260627
```

Support summary:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_010_velocity_contrast_cross_track_guard_support_summary.json
```

Key support result:

| metric | value |
|---|---:|
| actual timesteps | 262,144 |
| steady-state steps/s | 1,228,583 |
| action distribution | `tanh_squashed_gaussian` |
| command generator profile | `velocity_contrast_constant_speed` |
| reward coefficients | `{"trajectory_cross_track_coef": 1.8}` |
| final eval reward | -3.2175 |
| final eval position error | 0.4690 |
| final eval velocity error | 0.7674 |
| final eval cross-track error | 0.3135 |
| final eval done mean | 0.0 |

The support smoke had finite metrics and positive short-run learning signal for
reward, position, cross-track, and done mean. It is not a performance judgment.

Checkpoint metadata confirms:

```text
task=reference_command_no_gate_reward
observation_layout=level3_reference_tracker_command_v3
obs_dim=56
action_distribution=tanh_squashed_gaussian
command_generator_profile=velocity_contrast_constant_speed
reward_coefficients={"trajectory_cross_track_coef": 1.8}
reward_scope=no gate/aperture/obstacle/race/finish/stage reward
```

## Support Audit

Audit:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_010_velocity_contrast_cross_track_guard_support_audit.json
```

Checkpoint scenario:

| audit item | result |
|---|---|
| action clipping | ok |
| action sampling/logprob | ok |
| advantage scale | ok |
| initial std | ok |
| reward scale | ok |
| stored-vs-env logprob abs mean | `3.159e-7` |
| sample clip fraction | `0.0` |

The untrained initial scenario still reports large advantage scale, which is
consistent with earlier support audits. The checkpoint scenario is the support
gate for launch and it is green.

## Checker

Read-only checker result:

```text
ALL GREEN
```

Checker verified:

```text
py_compile passed
trajectory_cross_track_coef accepted
gate_cross_bonus and obstacle_coef rejected
support summary finite
checkpoint metadata correct
audit checkpoint scenario all ok
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
generated checkpoints / W&B / tracker_stage_metrics artifacts not staged
```

## Conclusion

Support passed. Launch `v62d_010_velocity_contrast_cross_track_guard_30m` from
scratch.

Do not interpret the support smoke as tracker qualification. The real evidence
must come from the 30M candidate, 5M milestones, best-checkpoint audit, three
reviewers, main decision packet, registry/state update, and reader note.
