# v62d_006 Long-Rollout Support

Date: 2026-06-27

## Purpose

Validate the support gate for `v62d_006_speedbin_longrollout_256x128_30m`
before launching a full 30M candidate.

This support step changes only PPO rollout geometry:

```text
1024 envs x 32 steps -> 256 envs x 128 steps
```

It keeps the same batch size (`32768`) but expands the temporal window from
about `0.64s` to about `2.56s` at 50 Hz.

## Support Smoke

Command:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_006_speedbin_longrollout_256x128_support \
  --config level3_tracker_free_space.toml \
  --seed 26460 \
  --num-envs 256 \
  --num-steps 128 \
  --total-timesteps 262144 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 131072 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_support/v62d_006_speedbin_longrollout_256x128_support_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_006_speedbin_longrollout_256x128_support_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --value-target-scale 1.0 \
  --eval-rollouts 4 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_006_speedbin_longrollout_256x128_support \
  --wandb-run-id v62d_006_speedbin_longrollout_256x128_support_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_006_speedbin_longrollout_256x128_support_20260627
```

Generated artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_006_speedbin_longrollout_256x128_support_summary.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_006_speedbin_longrollout_256x128_support_audit.json
lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_support/
wandb/run-20260627_143951-v62d_006_speedbin_longrollout_256x128_support_20260627/
```

## Smoke Result

Support smoke completed `262,144` steps and wrote a loadable checkpoint.

Key result:

| metric | value |
|---|---:|
| actual timesteps | 262,144 |
| steady-state steps/s | 413,322 |
| steady-state vs PyTorch fast path | 10.38x |
| all finite | 1.0 |
| action clip fraction | 0.0 |
| action/logprob consistency error | 3.14e-7 |
| final eval reward | -4.8894 |
| final eval position error | 0.6533 |
| final eval velocity error | 0.7279 |
| final eval cross-track error | 0.5246 |
| final eval done mean | 0.00401 |

The longer rollout is slower than `1024x32`, but still fast enough for a 30M
candidate. The first two updates include compilation/autotune cost; steady-state
updates are about `0.079s`.

## Metadata Readback

The support checkpoint metadata records:

```text
format: v62_brax_reference_command_tracker
global_step: 262144
num_envs: 256
num_steps: 128
observation_layout: level3_reference_tracker_command_v3
action_distribution: tanh_squashed_gaussian
action_logprob_mode: tanh_squashed_gaussian_logprob_with_jacobian
command_generator_profile: speed_bin_balanced
reward_coefficients: {}
value_target_scale: 1.0
reward_scope: no gate/aperture/obstacle/race/finish/stage reward
```

This verifies the support lane did not change actor observation layout, action
distribution, reward semantics, or config semantics.

## Audit

Support audit command:

```bash
pixi run -e gpu python scripts/audit_v62b_brax_ppo_signals.py \
  --config level3_tracker_free_space.toml \
  --seed 26462 \
  --num-envs 256 \
  --num-steps 128 \
  --checkpoint lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_support/v62d_006_speedbin_longrollout_256x128_support_final.pkl \
  --initial-log-std-values=-2.0 \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_006_speedbin_longrollout_256x128_support_audit.json \
  --jax-device gpu
```

Checkpoint audit verdicts:

```text
action_clipping: ok
action_sampling_logprob: ok
advantage_scale: large
initial_std: ok
reward_scale: large
stored_vs_env_logprob_abs_mean: 3.17e-7
sample_clip_fraction: 0.0
```

The large advantage/reward scale is expected evidence from the longer
`256x128` horizon and is not a support blocker. It does mean the 30M candidate
must be monitored closely for value loss, return/advantage scale, explained
variance, and velocity obedience.

## Checker

Read-only checker result:

```text
ALL GREEN
```

Checker verified:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
checkpoint metadata num_envs=256 and num_steps=128
observation_layout=level3_reference_tracker_command_v3
action_distribution=tanh_squashed_gaussian
command_generator_profile=speed_bin_balanced
reward_coefficients={}
value_target_scale=1.0
finite summary/audit metrics
action_clipping=ok
action_sampling_logprob=ok
```

## Support Decision

Support passes. Launching the 30M candidate is approved by:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_006_support_decision.md
```

