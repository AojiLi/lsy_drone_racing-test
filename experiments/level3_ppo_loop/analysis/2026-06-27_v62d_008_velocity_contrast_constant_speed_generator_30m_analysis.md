# v62d_008 Velocity-Contrast Constant-Speed Generator 30M Analysis

Date: 2026-06-27

## Purpose

Evaluate candidate:

```text
v62d_008_velocity_contrast_constant_speed_generator_30m
```

Family:

```text
C_generator_velocity_distribution
```

Hypothesis:

```text
Use paired low/medium/high desired-speed contrast windows and longer
constant-speed segments so the actor must obey desired_velocity/desired_speed
instead of solving the task mostly through position tracking.
```

This is a bottom-tracker free-space command-following run, not a Level3 hard
eval.

## Training Command

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_008_velocity_contrast_constant_speed_generator_30m \
  --config level3_tracker_free_space.toml \
  --seed 26481 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_008_velocity_contrast_constant_speed_generator_30m/v62d_008_velocity_contrast_constant_speed_generator_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_generator_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile velocity_contrast_constant_speed \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_008_velocity_contrast_constant_speed_generator_30m \
  --wandb-run-id v62d_008_velocity_contrast_constant_speed_generator_30m_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_008_velocity_contrast_constant_speed_generator_30m_20260627
```

Training completed `30,015,488` steps from scratch. Steady-state throughput was
about `1.281M env steps/s`, roughly `32.2x` the PyTorch fast path.

## Eval Protocol

Generated milestone artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_generator_30m_summary.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_generator_30m_milestone_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_generator_30m_milestone_eval.csv
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_generator_30m_best_audit.json
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
reward_coefficients: {}
```

## Milestone Results

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| v62c 7M baseline | -4.8459 | 0.6573 | 0.5214 | 0.7397 | 0.00391 | 0.000006 | -7.5365 |
| 5M | -5.2070 | 0.7235 | 0.5164 | 0.8642 | 0.00391 | 0.000023 | -8.1158 |
| 10M | -5.3968 | 0.6148 | 0.4614 | 1.0099 | 0.00586 | 0.000061 | -8.1346 |
| 15M | -5.5725 | 0.8241 | 0.6173 | 0.7832 | 0.00391 | 0.000052 | -8.7733 |
| 20M | -5.3774 | 0.7979 | 0.5900 | 0.7455 | 0.00391 | 0.000040 | -8.4565 |
| 25M | -6.7173 | 0.4285 | 0.3735 | 0.7961 | 0.01495 | 0.000135 | -8.8813 |
| 30M | -4.6294 | 0.7943 | 0.5449 | 0.5708 | 0.00219 | 0.000016 | -7.4853 |
| final | -4.6294 | 0.7943 | 0.5449 | 0.5708 | 0.00219 | 0.000016 | -7.4853 |

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

Best checkpoint inside v62d_008:

```text
30M
lsy_drone_racing/control/checkpoints/v62d_008_velocity_contrast_constant_speed_generator_30m/v62d_008_velocity_contrast_constant_speed_generator_30m_step_030000000.pkl
```

Best metrics:

```text
reward_mean = -4.6294
command_position_error = 0.7943
cross_track_error = 0.5449
command_velocity_error = 0.5708
done_mean = 0.00219
action_delta_penalty = 0.0000155
balanced_score = -7.4853
```

Compared with v62c 7M:

```text
velocity error improves by 22.84%
position error worsens by 20.84%
cross-track worsens by 4.50%
done mean improves by 0.00171
action delta is 2.43x higher but still small in absolute terms
```

## Audit

Best-checkpoint audit:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_008_velocity_contrast_constant_speed_generator_30m_best_audit.json
```

Checkpoint audit verdicts:

```text
action_clipping=ok
action_sampling_logprob=ok
advantage_scale=ok
initial_std=ok
reward_scale=ok
stored_vs_env_logprob_abs_mean=3.26e-7
sample_clip_fraction=0.0
```

PPO caveat:

```text
checkpoint return mean/std = -281.57 / 5.76
checkpoint value mean/std = -284.09 / 0.00081
```

The critic remains almost state-constant. This did not break action/logprob
validity, but it is still a PPO-quality issue for later candidates.

## Review Summary

Three reviews were written in:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_008_velocity_contrast_constant_speed_generator_30m_subagent_reviews.md
```

Summary:

- `tracker_eval_metrics` supports promotion because v62d_008 is the first
  candidate to clear the velocity bar and has a slightly better balanced score.
- `tracker_wandb_ppo` says the run is trustworthy and useful, but not a balanced
  tracker solution or 60M candidate because spatial tracking drifted and the
  critic remains weak.
- `tracker_structure_research` recommends no promotion because the position
  regression violates the user goal's promotion contract, and proposes a
  guarded velocity-contrast generator next.

## Main-Agent Conclusion

Do not promote v62d_008 as current best. The original promotion contract says a
candidate may promote only if velocity improves by 10%-15% while position and
cross-track do not worsen by more than 5%. v62d_008 clears the velocity gate
strongly, but its best checkpoint worsens position by `20.84%`.

This is not a failed direction. It is the first strong evidence that generator
contrast can teach velocity obedience. The next candidate should keep that
signal while restoring spatial discipline from the earlier speed-bin generator.

Decision:

```text
launch_best_of_family_combination
```

Next candidate:

```text
v62d_009_velocity_contrast_spatial_guarded_generator
```

It must use builder/checker support before 30M because it changes generator
semantics.
