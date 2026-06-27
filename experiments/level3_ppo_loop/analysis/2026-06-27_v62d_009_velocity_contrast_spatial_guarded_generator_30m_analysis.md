# v62d_009 Velocity-Contrast Spatial-Guarded Generator 30M Analysis

Date: 2026-06-27

## Purpose

Evaluate candidate:

```text
v62d_009_velocity_contrast_spatial_guarded_generator_30m
```

Family:

```text
E_best_of_family_combination
```

Hypothesis:

```text
Keep v62d_008's low/medium/high velocity contrast, but restore spatial
discipline by shortening pass/slow/recover distances and moving deceleration
toward speed-bin-like behavior.
```

This is a bottom-tracker free-space command-following run, not a Level3 hard
eval.

## Training Command

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

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_009_velocity_contrast_spatial_guarded_generator_30m_20260627
```

Training completed `30,015,488` steps from scratch. Steady-state throughput was
about `1.276M env steps/s`, roughly `32.05x` the PyTorch fast path.

## Eval Protocol

Generated milestone artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_009_velocity_contrast_spatial_guarded_generator_30m_summary.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_009_velocity_contrast_spatial_guarded_generator_30m_milestone_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_009_velocity_contrast_spatial_guarded_generator_30m_milestone_eval.csv
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_009_velocity_contrast_spatial_guarded_generator_30m_best_audit.json
```

Milestones were evaluated at `5M / 10M / 15M / 20M / 25M / 30M / final` with:

```text
config: level3_tracker_free_space.toml
seed: 26310
num_envs: 1024
num_steps: 32
eval_rollouts: 16
action_distribution: tanh_squashed_gaussian
command_generator_profile: velocity_contrast_spatial_guarded
reward_coefficients: {}
```

## Milestone Results

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| v62c 7M baseline | -4.8459 | 0.6573 | 0.5214 | 0.7397 | 0.00391 | 0.000006 | -7.5365 |
| v62d_008 30M | -4.6294 | 0.7943 | 0.5449 | 0.5708 | 0.00219 | 0.000016 | -7.4853 |
| 5M | -5.6197 | 0.6704 | 0.5222 | 0.8935 | 0.00586 | 0.000015 | -8.4724 |
| 10M | -5.0505 | 0.7073 | 0.5409 | 0.7398 | 0.00391 | 0.000004 | -7.8704 |
| 15M | -4.8927 | 0.6570 | 0.4833 | 0.7811 | 0.00391 | 0.000012 | -7.5566 |
| 20M | -6.2371 | 0.7669 | 0.6053 | 1.0065 | 0.00586 | 0.000068 | -9.4926 |
| 25M | -6.5265 | 0.9361 | 0.7327 | 1.0339 | 0.00391 | 0.000060 | -10.3123 |
| 30M | -5.3838 | 0.9161 | 0.7357 | 0.7021 | 0.00195 | 0.000029 | -8.8657 |
| final | -5.3838 | 0.9161 | 0.7357 | 0.7021 | 0.00195 | 0.000029 | -8.8657 |

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

Best balanced checkpoint inside v62d_009:

```text
15M
lsy_drone_racing/control/checkpoints/v62d_009_velocity_contrast_spatial_guarded_generator_30m/v62d_009_velocity_contrast_spatial_guarded_generator_30m_step_015000000.pkl
```

Best balanced metrics:

```text
reward_mean = -4.8927
command_position_error = 0.6570
cross_track_error = 0.4833
command_velocity_error = 0.7811
done_mean = 0.00391
action_delta_penalty = 0.0000122
balanced_score = -7.5566
```

Compared with v62c 7M:

```text
velocity error worsens by 5.59%
position error is effectively tied / 0.04% better
cross-track improves by 7.31%
done mean is tied
action delta is about 1.9x higher but still tiny in absolute terms
balanced score is slightly worse by 0.0202
```

Best velocity checkpoint inside v62d_009:

```text
30M / final
command_velocity_error = 0.7021
```

That improves velocity by only about `5.08%` versus v62c 7M, below the
`10%-15%` promotion threshold, and it badly regresses position and cross-track:

```text
position error: 0.6573 -> 0.9161
cross-track error: 0.5214 -> 0.7357
```

## Audit

Best-checkpoint audit:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_009_velocity_contrast_spatial_guarded_generator_30m_best_audit.json
```

Checkpoint audit verdicts for the `15M` checkpoint:

```text
action_clipping=ok
action_sampling_logprob=ok
advantage_scale=ok
initial_std=ok
reward_scale=ok
stored_vs_env_logprob_abs_mean=3.18e-7
sample_clip_fraction=0.0
```

PPO caveat:

```text
checkpoint return mean/std = -153.72 / 4.86
checkpoint value mean/std = -143.87 / 0.00298
final train-batch value mean/std = -284.75 / 0.00252
final train-batch return mean/std = -311.89 / 41.07
final explained variance ~= 5.45e-5
```

The critic remains almost state-constant. This is now a repeated v62d pattern,
not a one-off v62d_009 artifact.

## Review Summary

Three reviews were written in:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_009_velocity_contrast_spatial_guarded_generator_30m_subagent_reviews.md
```

Summary:

- `tracker_eval_metrics`: do not promote. The best balanced checkpoint restores
  spatial discipline but worsens velocity. The best velocity checkpoint fails
  the `10%-15%` velocity threshold and collapses spatial tracking.
- `tracker_wandb_ppo`: do not continue as-is to 60M. PPO action/logprob plumbing
  is clean, but the run drifts after 15M and the critic remains weak.
- `tracker_structure_research`: reject and pause for a v62d meta-review rather
  than launching another immediate generator-only candidate. The data now shows
  a spatial/velocity tradeoff and repeated critic-quality symptoms.

## Decision-Relevant Interpretation

v62d_009 answered the v62d_008 question:

```text
Can spatial guards preserve v62d_008's velocity breakthrough while fixing
position/cross-track?
```

The answer is no. The candidate can either:

```text
restore spatial tracking at 15M but lose the velocity gain
```

or:

```text
recover a small amount of velocity by 30M while sacrificing spatial tracking
```

It therefore does not beat the v62c 7M frontier and does not become the current
best. The immediate search should not blindly continue generator-only variants.
The next useful step is a v62d meta-review focused on the velocity/spatial
tradeoff and the weak critic/value-scale pattern across candidates.
