# v62d_008 Velocity-Contrast Constant-Speed Support

Date: 2026-06-27

## Purpose

Validate support for the next high-budget generic reference-tracker candidate:

```text
v62d_008_velocity_contrast_constant_speed_generator_30m
```

This is Family C: generator velocity distribution. It changes only the clean
v60/v62 command-reference generator when explicitly enabled:

```text
--command-generator-profile velocity_contrast_constant_speed
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
velocity_contrast_constant_speed
```

The formal trainer and audit scripts already use:

```text
choices=v60_rollout.COMMAND_GENERATOR_PROFILES
```

so the new profile is available to:

- `scripts/train_v62_brax_reference_command_tracker.py`
- `scripts/audit_v62b_brax_ppo_signals.py`

The profile intentionally over-samples low/medium/high speed contrasts and
longer constant-speed windows while preserving the clean command-tracker
interface.

Sampled support stats from 4096 plans:

| metric | mean | p05 | p50 | p95 |
|---|---:|---:|---:|---:|
| pass speed | 0.5798 | 0.3375 | 0.5738 | 0.8534 |
| brake-entry speed | 0.1787 | 0.1022 | - | 0.2400 |
| hold speed | 0.0253 | - | - | 0.0475 |
| slow-through speed | 0.2725 | 0.1688 | - | 0.3860 |
| recover speed | 0.5743 | 0.3575 | - | 0.8322 |
| total plan steps | 341.6 | - | 323.5 | 478.0 |

## Builder Checks

Syntax check:

```bash
pixi run -e gpu python -m py_compile \
  scripts/benchmark_v60_brax_rollout.py \
  scripts/train_v62_brax_reference_command_tracker.py \
  scripts/train_v60_brax_ppo_smoke.py \
  scripts/audit_v62b_brax_ppo_signals.py
```

Result:

```text
passed
```

Small rollout benchmark:

```bash
pixi run -e gpu python scripts/benchmark_v60_brax_rollout.py \
  --config level3_tracker_free_space.toml \
  --seed 26480 \
  --num-envs 256 \
  --num-steps 32 \
  --repeat 2 \
  --command-generator-profile velocity_contrast_constant_speed \
  --jax-device gpu
```

Result:

```text
finite rollout
reward_mean_last=-3.6822
done_mean_last=0.0
obs_abs_mean_last=0.2272
```

## Support Smoke

Command:

```bash
mkdir -p lsy_drone_racing/control/checkpoints/v62d_008_velocity_contrast_constant_speed_support \
  experiments/level3_ppo_loop/analysis/tracker_stage_metrics && \
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_008_velocity_contrast_constant_speed_support \
  --config level3_tracker_free_space.toml \
  --seed 26480 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 262144 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 131072 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_008_velocity_contrast_constant_speed_support/v62d_008_velocity_contrast_constant_speed_support_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_support_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile velocity_contrast_constant_speed \
  --value-target-scale 1.0 \
  --eval-rollouts 4 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_008_velocity_contrast_constant_speed_support \
  --wandb-run-id v62d_008_velocity_contrast_constant_speed_support_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_008_velocity_contrast_constant_speed_support_20260627
```

Generated artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_support_summary.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_support_audit.json
lsy_drone_racing/control/checkpoints/v62d_008_velocity_contrast_constant_speed_support/
wandb/run-20260627_*
```

## Smoke Result

Support smoke completed `262,144` steps and wrote a loadable checkpoint.

| metric | value |
|---|---:|
| actual timesteps | 262,144 |
| steady-state steps/s | 1,258,804 |
| steady-state vs PyTorch fast path | 31.63x |
| all finite | 1.0 |
| action clip fraction | 0.0 |
| action/logprob consistency error | 3.17e-7 |
| reward coefficients | `{}` |
| initial eval reward | -3.1459 |
| final eval reward | -3.1854 |
| initial position error | 0.5573 |
| final position error | 0.5013 |
| initial velocity error | 0.5929 |
| final velocity error | 0.8039 |
| initial cross-track error | 0.3458 |
| final cross-track error | 0.3195 |
| final done mean | 0.0000 |

This support smoke is plumbing evidence only. It should not be used to promote
or reject the full candidate. The short smoke improved position/cross-track
metrics but worsened velocity, which is acceptable for a support gate and must
be judged only after the required 30M candidate run.

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
command_generator_profile: velocity_contrast_constant_speed
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
  --seed 26482 \
  --num-envs 1024 \
  --num-steps 32 \
  --checkpoint lsy_drone_racing/control/checkpoints/v62d_008_velocity_contrast_constant_speed_support/v62d_008_velocity_contrast_constant_speed_support_final.pkl \
  --initial-log-std-values=-2.0 \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile velocity_contrast_constant_speed \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_support_audit.json \
  --jax-device gpu
```

Checkpoint audit verdicts:

```text
action_clipping: ok
action_sampling_logprob: ok
advantage_scale: ok
initial_std: ok
reward_scale: ok
stored_vs_env_logprob_abs_mean: 3.11e-7
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
diff limited to scripts/benchmark_v60_brax_rollout.py
COMMAND_GENERATOR_PROFILES includes velocity_contrast_constant_speed
trainer and audit consume the shared profile choices
summary records command_generator_profile=velocity_contrast_constant_speed
summary records action_distribution=tanh_squashed_gaussian
summary records reward_coefficients={}
checkpoint metadata records level3_reference_tracker_command_v3
checkpoint metadata records tanh_squashed_gaussian
checkpoint metadata records num_envs=1024 and num_steps=32
checkpoint metadata records value_target_scale=1.0
audit action_clipping=ok
audit action_sampling_logprob=ok
stored_vs_env_logprob_abs_mean ~= 3e-7
py_compile/json/diff checks passed
```

## Support Decision

Support passes. Launch the bounded 30M candidate from scratch:

```text
v62d_008_velocity_contrast_constant_speed_generator_30m
```

The 30M command is recorded in:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_008_support_decision.md
```

Do not promote or reject the candidate from this support smoke. Judge it only
after the full 30M run, milestone eval, best-checkpoint audit, and three-review
analysis.
