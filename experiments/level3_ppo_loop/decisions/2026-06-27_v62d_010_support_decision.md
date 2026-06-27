# v62d_010 Support Decision

Date: 2026-06-27

Decision outcome:

```text
continue_same_family_with_new_knob
```

Support status:

```text
passed
```

Approved training candidate:

```text
v62d_010_velocity_contrast_cross_track_guard_30m
```

## Why Launch

The support gate proved that the trainer and audit can safely carry:

```text
--reward-coeff trajectory_cross_track_coef=1.8
```

without changing the actor observation, action distribution, config files, or
reward scope.

Checker independently returned:

```text
ALL GREEN
```

## Training Command

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_010_velocity_contrast_cross_track_guard_30m \
  --config level3_tracker_free_space.toml \
  --seed 26501 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_010_velocity_contrast_cross_track_guard_30m/v62d_010_velocity_contrast_cross_track_guard_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_010_velocity_contrast_cross_track_guard_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile velocity_contrast_constant_speed \
  --reward-coeff trajectory_cross_track_coef=1.8 \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_010_velocity_contrast_cross_track_guard_30m \
  --wandb-run-id v62d_010_velocity_contrast_cross_track_guard_30m_20260627 \
  --jax-device gpu
```

## Hard Boundaries

The candidate must keep:

```text
action_distribution=tanh_squashed_gaussian
actor observation=level3_reference_tracker_command_v3
command_generator_profile=velocity_contrast_constant_speed
trajectory_cross_track_coef=1.8
value_target_scale=1.0
```

Do not modify:

```text
config/level3.toml
config/level3_tracker_free_space.toml
```

Do not add:

```text
gate reward
aperture reward
race reward
finish reward
stage reward
gate/obstacle/planner-phase actor input
```

## Required Post-Run Work

After training:

```text
evaluate 5M/10M/15M/20M/25M/30M/final
select best checkpoint by multi-metric score
run action/logprob/value audit on best checkpoint
run exactly three reviewers
write analysis packet
write decision packet
write Chinese reader note
update registry/state/AGENTS
commit and push intended small files
```
