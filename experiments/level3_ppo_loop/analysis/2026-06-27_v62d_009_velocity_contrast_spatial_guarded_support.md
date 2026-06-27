# v62d_009 Velocity-Contrast Spatial-Guarded Support

Date: 2026-06-27

## Purpose

Validate support for the next high-budget generic reference-tracker candidate:

```text
v62d_009_velocity_contrast_spatial_guarded_generator_30m
```

This is Family E: a best-of-family command-generator combination. It changes
only the clean v60/v62 command-reference generator when explicitly enabled:

```text
--command-generator-profile velocity_contrast_spatial_guarded
```

It does not change actor observation layout, action distribution, reward
semantics, PPO update settings, or either Level3 config.

## Implemented Support

Changed file:

```text
scripts/benchmark_v60_brax_rollout.py
```

New profile:

```text
velocity_contrast_spatial_guarded
```

The profile keeps the paired low/medium/high speed contrast from v62d_008, but
shortens the generated pass/slow/recover distances and moves the deceleration
fraction back toward the speed-bin family:

```text
pass_dist: 0.44-0.76
slow_dist: 0.32-0.62
recover_dist: 0.42-0.78
decel_fraction: 0.44
pass_decel_min_steps: 38
slow_min_steps: 58
recover_min_steps: 52
```

The formal trainer and audit scripts already use:

```text
choices=v60_rollout.COMMAND_GENERATOR_PROFILES
```

so the new profile is available to:

- `scripts/train_v62_brax_reference_command_tracker.py`
- `scripts/audit_v62b_brax_ppo_signals.py`

## Builder Checks

Syntax check:

```bash
pixi run -e gpu python -m py_compile \
  scripts/benchmark_v60_brax_rollout.py \
  scripts/train_v62_brax_reference_command_tracker.py \
  scripts/audit_v62b_brax_ppo_signals.py \
  scripts/train_v60_brax_ppo_smoke.py
```

Result:

```text
passed
```

Profile exposure check:

```text
COMMAND_GENERATOR_PROFILES includes velocity_contrast_spatial_guarded
```

Sampled support stats from 4096 plans:

| metric | mean | min | p50 | max |
|---|---:|---:|---:|---:|
| pass speed | 0.5865 | 0.3201 | 0.5805 | 0.8799 |
| brake-entry speed | 0.1808 | 0.1000 | 0.1854 | 0.2400 |
| hold speed | 0.0249 | 0.0000 | 0.0249 | 0.0500 |
| slow-through speed | 0.2752 | 0.1601 | 0.2750 | 0.4000 |
| recover speed | 0.5809 | 0.3400 | 0.5698 | 0.8599 |
| pass steps | 76.43 | 50 | 68 | 153 |
| hold steps | 60.03 | 44 | 60 | 76 |
| slow steps | 92.77 | 58 | 86 | 194 |
| recover steps | 67.55 | 52 | 58 | 151 |
| total plan steps | 296.79 | 205 | - | 524 |

Small rollout benchmark:

```bash
pixi run -e gpu python scripts/benchmark_v60_brax_rollout.py \
  --config level3_tracker_free_space.toml \
  --seed 26491 \
  --num-envs 1024 \
  --num-steps 32 \
  --repeat 2 \
  --command-generator-profile velocity_contrast_spatial_guarded \
  --jax-device gpu
```

Result:

```text
finite rollout
second rollout time: 0.020846s for 32768 env steps
reward_mean_last=-3.5257
done_mean_last=0.0
obs_abs_mean_last=0.2339
```

## Support Smoke

Command:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_009_velocity_contrast_spatial_guarded_support \
  --config level3_tracker_free_space.toml \
  --seed 26490 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 262144 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --value-target-scale 1.0 \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile velocity_contrast_spatial_guarded \
  --checkpoint-interval 262144 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_009_velocity_contrast_spatial_guarded_support/v62d_009_velocity_contrast_spatial_guarded_support_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_009_velocity_contrast_spatial_guarded_support_summary.json \
  --eval-rollouts 4 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_009_velocity_contrast_spatial_guarded_support \
  --wandb-run-id v62d_009_velocity_contrast_spatial_guarded_support_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_009_velocity_contrast_spatial_guarded_support_20260627
```

Generated artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_009_velocity_contrast_spatial_guarded_support_summary.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_009_velocity_contrast_spatial_guarded_support_audit.json
lsy_drone_racing/control/checkpoints/v62d_009_velocity_contrast_spatial_guarded_support/
wandb/run-20260627_*
```

## Smoke Result

Support smoke completed `262,144` steps and wrote a loadable checkpoint.

| metric | value |
|---|---:|
| actual timesteps | 262,144 |
| steady-state steps/s | 1,208,481 |
| steady-state vs PyTorch fast path | 30.36x |
| all finite | 1.0 |
| action clip fraction | 0.0 |
| action/logprob consistency error | 3.15e-7 |
| reward coefficients | `{}` |
| initial eval reward | -3.3960 |
| final eval reward | -2.7398 |
| initial position error | 0.5443 |
| final position error | 0.4260 |
| initial velocity error | 0.4933 |
| final velocity error | 0.6544 |
| initial cross-track error | 0.4197 |
| final cross-track error | 0.2492 |
| final done mean | 0.0000 |

This support smoke is plumbing evidence only. It should not be used to promote
or reject the full candidate. The short smoke improved reward, position,
cross-track, and done rate, but worsened velocity, which is acceptable for a
support gate and must be judged only after the required 30M candidate run.

## Metadata Readback

The support checkpoint records:

```text
format: v62_brax_reference_command_tracker
global_step: 262144
num_envs: 1024
num_steps: 32
observation_layout: level3_reference_tracker_command_v3
action_distribution: tanh_squashed_gaussian
action_logprob_mode: tanh_squashed_gaussian_logprob_with_jacobian
command_generator_profile: velocity_contrast_spatial_guarded
reward_coefficients: {}
value_target_scale: 1.0
reward_scope: no gate/aperture/obstacle/race/finish/stage reward
```

This verifies the support lane did not change actor observation layout, action
distribution, reward coefficients, or no-gate tracker boundaries.

## Audit

Support audit command:

```bash
pixi run -e gpu python scripts/audit_v62b_brax_ppo_signals.py \
  --config level3_tracker_free_space.toml \
  --seed 26492 \
  --num-envs 1024 \
  --num-steps 32 \
  --checkpoint lsy_drone_racing/control/checkpoints/v62d_009_velocity_contrast_spatial_guarded_support/v62d_009_velocity_contrast_spatial_guarded_support_final.pkl \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_009_velocity_contrast_spatial_guarded_support_audit.json \
  --command-generator-profile velocity_contrast_spatial_guarded \
  --action-distribution tanh_squashed_gaussian \
  --initial-log-std-values=-2.0 \
  --jax-device gpu
```

Checkpoint audit verdicts:

```text
action_clipping: ok
action_sampling_logprob: ok
advantage_scale: ok
initial_std: ok
reward_scale: ok
stored_vs_env_logprob_abs_mean: 3.16e-7
sample_clip_fraction: 0.0
```

## Checker

Read-only checker result:

```text
ALL GREEN
```

Checker verified:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
COMMAND_GENERATOR_PROFILES includes velocity_contrast_spatial_guarded
trainer and audit accept the profile through shared choices
checkpoint metadata records command_generator_profile=velocity_contrast_spatial_guarded
observation_layout remains level3_reference_tracker_command_v3
action_distribution remains tanh_squashed_gaussian
reward_coefficients remain {}
diff is limited to scripts/benchmark_v60_brax_rollout.py
no gate/aperture/obstacle/race/finish/stage reward or input change was introduced
support summary JSON is finite
support audit verdicts are all ok
```

## Conclusion

Support passes. Launch the bounded 30M candidate from scratch only through the
approved support decision command.
