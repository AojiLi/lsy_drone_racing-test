# v62d_009 Support Decision

Date: 2026-06-27

## Decision

Support passes.

Launch the bounded 30M candidate from scratch:

```text
v62d_009_velocity_contrast_spatial_guarded_generator_30m
```

## Candidate

```text
v62d_009_velocity_contrast_spatial_guarded_generator_30m
```

Family:

```text
E_best_of_family_combination
```

Changed knob:

```text
command_generator_profile=velocity_contrast_spatial_guarded
```

Everything else remains at the v62d default:

```text
observation_layout=level3_reference_tracker_command_v3
action_distribution=tanh_squashed_gaussian
command_vel_error_coef=default
value_target_scale=1.0
num_envs=1024
num_steps=32
num_minibatches=4
update_epochs=1
train_from_scratch=true
```

## Support Evidence

Support packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_009_velocity_contrast_spatial_guarded_support.md
```

Support smoke completed `262,144` steps with:

```text
command_generator_profile=velocity_contrast_spatial_guarded
action_distribution=tanh_squashed_gaussian
reward_coefficients={}
actual_timesteps=262144
steady_state_steps_per_s=1208481
all_finite=1.0
action_clip_fraction=0.0
action/logprob consistency ~= 3.15e-7
```

Checkpoint metadata records:

```text
observation_layout=level3_reference_tracker_command_v3
action_distribution=tanh_squashed_gaussian
command_generator_profile=velocity_contrast_spatial_guarded
reward_coefficients={}
num_envs=1024
num_steps=32
value_target_scale=1.0
```

Support audit passed:

```text
action_clipping=ok
action_sampling_logprob=ok
advantage_scale=ok
initial_std=ok
reward_scale=ok
stored_vs_env_logprob_abs_mean=3.16e-7
```

Read-only checker result:

```text
ALL GREEN
```

Checker verified:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
diff limited to scripts/benchmark_v60_brax_rollout.py
trainer/audit profile choices include velocity_contrast_spatial_guarded
summary and checkpoint metadata record the intended profile
observation_layout remains level3_reference_tracker_command_v3
action_distribution remains tanh_squashed_gaussian
reward_coefficients remain {}
action/logprob audit passes
```

Both target configs must remain unchanged:

```text
config/level3.toml
config/level3_tracker_free_space.toml
```

## Approved Command After Checker Passes

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_009_velocity_contrast_spatial_guarded_generator_30m \
  --config level3_tracker_free_space.toml \
  --seed 26491 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_009_velocity_contrast_spatial_guarded_generator_30m/v62d_009_velocity_contrast_spatial_guarded_generator_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_009_velocity_contrast_spatial_guarded_generator_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile velocity_contrast_spatial_guarded \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_009_velocity_contrast_spatial_guarded_generator_30m \
  --wandb-run-id v62d_009_velocity_contrast_spatial_guarded_generator_30m_20260627 \
  --jax-device gpu
```

This command trains from scratch, saves 5M milestones, uses online W&B, and
meets the v62d high-budget candidate minimum of at least 30M timesteps.
