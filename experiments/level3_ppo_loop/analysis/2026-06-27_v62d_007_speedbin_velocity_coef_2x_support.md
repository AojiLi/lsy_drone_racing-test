# v62d_007 Speed-Bin Velocity Coef 2x Support

Date: 2026-06-27

## Purpose

Validate support for `v62d_007_speedbin_velocity_coef_2x_30m` before launching a
full 30M candidate.

This candidate is a best-of-family combination:

```text
speed_bin_balanced command generator
+ generic command velocity-error coefficient 1.2
```

No actor observation layout, action distribution, Level3 config, or gate/race
reward semantics changed.

## Support Code Fix

The training script already supported:

```text
--command-vel-error-coef
```

The support audit script did not. A small evaluator-support patch added the same
CLI argument to:

```text
scripts/audit_v62b_brax_ppo_signals.py
```

and passed `ppo_smoke.command_reward_coefficients(args)` into the audit
`build_command_env_step` call. This lets support audits inspect the same generic
command reward coefficient used by training.

This is an evaluator/audit support change only. It does not alter the default
audit behavior when the flag is omitted.

## Support Smoke

Command:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_007_speedbin_velocity_coef_2x_support \
  --config level3_tracker_free_space.toml \
  --seed 26470 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 262144 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 131072 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_support/v62d_007_speedbin_velocity_coef_2x_support_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_support_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --command-vel-error-coef 1.2 \
  --value-target-scale 1.0 \
  --eval-rollouts 4 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_007_speedbin_velocity_coef_2x_support \
  --wandb-run-id v62d_007_speedbin_velocity_coef_2x_support_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_007_speedbin_velocity_coef_2x_support_20260627
```

Generated artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_support_summary.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_support_audit.json
lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_support/
wandb/run-20260627_151248-v62d_007_speedbin_velocity_coef_2x_support_20260627/
```

## Smoke Result

Support smoke completed `262,144` steps and wrote a loadable checkpoint.

Key result:

| metric | value |
|---|---:|
| actual timesteps | 262,144 |
| steady-state steps/s | 1,182,853 |
| steady-state vs PyTorch fast path | 29.72x |
| all finite | 1.0 |
| action clip fraction | 0.0 |
| action/logprob consistency error | 3.15e-7 |
| reward coefficients | `{"vel_error_coef": 1.2}` |
| final eval reward | -3.7755 |
| final eval position error | 0.5122 |
| final eval velocity error | 0.7791 |
| final eval cross-track error | 0.3174 |
| final eval done mean | 0.0000 |

This support smoke is plumbing evidence, not a learning conclusion.

## Metadata Readback

The support checkpoint metadata records:

```text
format: v62_brax_reference_command_tracker
global_step: 262144
num_envs: 1024
num_steps: 32
observation_layout: level3_reference_tracker_command_v3
action_distribution: tanh_squashed_gaussian
command_generator_profile: speed_bin_balanced
reward_coefficients: {"vel_error_coef": 1.2}
value_target_scale: 1.0
reward_scope: no gate/aperture/obstacle/race/finish/stage reward
```

This verifies the combined knob is recorded in the checkpoint and does not
change actor observation layout or action distribution.

## Audit

Support audit command:

```bash
pixi run -e gpu python scripts/audit_v62b_brax_ppo_signals.py \
  --config level3_tracker_free_space.toml \
  --seed 26472 \
  --num-envs 1024 \
  --num-steps 32 \
  --checkpoint lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_support/v62d_007_speedbin_velocity_coef_2x_support_final.pkl \
  --initial-log-std-values=-2.0 \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --command-vel-error-coef 1.2 \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_support_audit.json \
  --jax-device gpu
```

Checkpoint audit verdicts:

```text
action_clipping: ok
action_sampling_logprob: ok
advantage_scale: large
initial_std: ok
reward_scale: ok
stored_vs_env_logprob_abs_mean: 3.12e-7
sample_clip_fraction: 0.0
```

`advantage_scale=large` is monitor-only for this short support run. It confirms
that value/return scale still needs attention during 30M analysis, but it does
not block support because action/logprob, reward-scale, finite-metric,
metadata, and config-boundary checks pass.

## Checker

Read-only checker result:

```text
ALL GREEN
```

Checker verified:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
audit script accepts and records --command-vel-error-coef
summary records command_generator_profile=speed_bin_balanced
summary records reward_coefficients={"vel_error_coef": 1.2}
checkpoint metadata records clean command-v3 observation and tanh action
checkpoint metadata records num_envs=1024 and num_steps=32
checkpoint metadata records reward_coefficients={"vel_error_coef": 1.2}
summary/audit metrics are finite
audit action_clipping=ok
audit action_sampling_logprob=ok
stored_vs_env_logprob_abs_mean ~= 3e-7
```

## Support Decision

Support passes. Launch the bounded 30M candidate from scratch:

```text
v62d_007_speedbin_velocity_coef_2x_30m
```

The 30M command is recorded in:

```text
experiments/level3_ppo_loop/v62d_candidates/v62d_007_hypothesis.md
```

Do not promote or reject the candidate from the support smoke. Judge it only
after the full 30M run, milestone eval, best-checkpoint audit, and three-review
analysis.
