# v62d_010 Velocity-Contrast Cross-Track Guard 30M Analysis

Date: 2026-06-27

## Purpose

Evaluate candidate:

```text
v62d_010_velocity_contrast_cross_track_guard_30m
```

Family:

```text
E_best_of_family_combination
```

Hypothesis:

```text
Keep v62d_008's velocity-contrast constant-speed command generator and add one
generic no-gate cross-track reward guard:

trajectory_cross_track_coef=1.8
```

The intended fix was:

```text
preserve v62d_008 velocity obedience
+ reduce pass-through spatial drift
```

This is a bottom-tracker free-space command-following run, not a Level3 hard
eval.

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

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_010_velocity_contrast_cross_track_guard_30m_20260627
```

Training completed `30,015,488` steps from scratch. Steady-state throughput was
about `1.273M env steps/s`, roughly `32x` the PyTorch fast path.

## Support Gate

Support packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_010_velocity_contrast_cross_track_guard_support.md
```

Decision packet:

```text
experiments/level3_ppo_loop/decisions/2026-06-27_v62d_010_support_decision.md
```

The builder/checker support gate passed before long training:

```text
safe --reward-coeff parsing added
trajectory_cross_track_coef=1.8 accepted
gate_cross_bonus and obstacle_coef rejected
checkpoint metadata records reward_coefficients
audit uses the same reward coefficients
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
```

## Eval Protocol

Generated milestone artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_010_velocity_contrast_cross_track_guard_30m_summary.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_010_velocity_contrast_cross_track_guard_30m_milestone_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_010_velocity_contrast_cross_track_guard_30m_milestone_eval.csv
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_010_velocity_contrast_cross_track_guard_30m_best_audit.json
```

Milestones were evaluated at `5M / 10M / 15M / 20M / 25M / 30M / final` with:

```text
config: level3_tracker_free_space.toml
seed: 26310
num_envs: 1024
num_steps: 32
eval_rollouts: 16
action_distribution: tanh_squashed_gaussian
command_generator_profile: velocity_contrast_constant_speed
reward_coefficients: {"trajectory_cross_track_coef": 1.8}
```

## Milestone Results

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| v62c 7M same profile | -5.4641 | 0.7297 | 0.5185 | 0.7954 | 0.00391 | 0.000006 | -8.3369 |
| v62d_008 30M same profile | -4.9563 | 0.7943 | 0.5449 | 0.5708 | 0.00219 | 0.000016 | -7.8122 |
| 5M | -5.8413 | 0.6613 | 0.4946 | 0.9339 | 0.00586 | 0.000018 | -8.6649 |
| 10M | -6.6387 | 0.9084 | 0.6806 | 0.9942 | 0.00391 | 0.000013 | -10.2611 |
| 15M | -7.3886 | 0.9178 | 0.6972 | 1.1398 | 0.00586 | 0.000042 | -11.1836 |
| 20M | -7.8099 | 1.0034 | 0.7774 | 1.1441 | 0.00586 | 0.000050 | -11.8995 |
| 25M | -6.1411 | 0.7033 | 0.5356 | 0.9993 | 0.00586 | 0.000053 | -9.1593 |
| 30M | -6.4548 | 0.9581 | 0.7451 | 0.6061 | 0.00452 | 0.000033 | -9.9886 |
| final | -6.4548 | 0.9581 | 0.7451 | 0.6061 | 0.00452 | 0.000033 | -9.9886 |

Balanced score:

```text
reward
- 2.0 * position_error
- 1.5 * cross_track_error
- 0.75 * velocity_error
- 10.0 * done_mean
- 2.0 * action_delta_penalty
```

## Best Checkpoint

Best balanced checkpoint inside v62d_010:

```text
5M
lsy_drone_racing/control/checkpoints/v62d_010_velocity_contrast_cross_track_guard_30m/v62d_010_velocity_contrast_cross_track_guard_30m_step_005000000.pkl
```

Best balanced metrics:

```text
reward_mean = -5.8413
command_position_error = 0.6613
cross_track_error = 0.4946
command_velocity_error = 0.9339
done_mean = 0.00586
action_delta_penalty = 0.0000179
balanced_score = -8.6649
```

Compared with the same-profile v62c 7M eval:

```text
position improves by 9.37%
cross-track improves by 4.61%
velocity worsens by 17.41%
done worsens from 0.00391 to 0.00586
balanced score is worse by 0.3284
```

Compared with v62d_008 30M under the same velocity-contrast profile:

```text
position improves by 16.75%
cross-track improves by 9.22%
velocity worsens by 63.62%
balanced score is worse by 0.8527
```

Best velocity checkpoint inside v62d_010:

```text
30M / final
command_velocity_error = 0.6061
```

This improves velocity by about `18.07%` versus the formal v62c 7M frontier,
but position and cross-track collapse:

```text
position error: 0.6573 -> 0.9581
cross-track error: 0.5214 -> 0.7451
```

It also does not beat v62d_008 on the velocity-contrast profile:

```text
v62d_008 30M velocity error = 0.5708
v62d_010 30M velocity error = 0.6061
```

## Audit

Best-checkpoint audit:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_010_velocity_contrast_cross_track_guard_30m_best_audit.json
```

Checkpoint audit verdicts for the `5M` checkpoint:

```text
action_clipping=ok
action_sampling_logprob=ok
advantage_scale=ok
initial_std=ok
reward_scale=ok
stored_vs_env_logprob_abs_mean=3.16e-7
sample_clip_fraction=0.0
```

PPO caveat:

```text
final explained variance ~= 5.81e-5
final values std ~= 0.00431
final returns std ~= 48.62
final value_loss ~= 1389.91
```

The action path is healthy enough to trust the result. The critic remains
almost state-constant, which is a repeated v62d pattern.

## Review Summary

Three reviews were written in:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_010_velocity_contrast_cross_track_guard_30m_subagent_reviews.md
```

Summary:

- `tracker_eval_metrics`: do not promote. The best checkpoint is `5M`, but it
  trades away velocity. The `30M/final` checkpoint recovers velocity only while
  losing spatial tracking.
- `tracker_wandb_ppo`: action/logprob/W&B/speed are healthy, but the critic is
  still weak. The negative result is trustworthy.
- `tracker_structure_research`: do not continue v62d_010 and do not launch
  v62d_011 immediately. Candidate 10 triggers a required 10-candidate
  meta-review before the next lane.

## Decision-Relevant Interpretation

v62d_010 tested:

```text
Can a generic cross-track reward guard preserve v62d_008's velocity obedience
while fixing pass-through spatial drift?
```

The answer is no. The candidate still splits into two modes:

```text
5M: spatial tracking improves, velocity obedience collapses
30M/final: velocity partially recovers, spatial tracking collapses
```

It therefore does not beat the v62c 7M frontier and does not preserve the
v62d_008 velocity breakthrough. The immediate search should pause for the
required 10-candidate v62d meta-review rather than launching v62d_011 directly.
