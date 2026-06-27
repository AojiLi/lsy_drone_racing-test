# v62d_007 Speed-Bin Velocity Coef 2x 30M Analysis

Date: 2026-06-27

## Purpose

Evaluate candidate:

```text
v62d_007_speedbin_velocity_coef_2x_30m
```

Family:

```text
E_best_of_family_combination
```

Hypothesis:

```text
Combine speed_bin_balanced command generation with generic command velocity
coefficient 1.2. v62d_004 had the best spatial/generator signal, and v62d_003
had the only direct velocity-coefficient signal.
```

This is a bottom-tracker free-space command-following run, not a Level3 hard
eval.

## Training Command

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_007_speedbin_velocity_coef_2x_30m \
  --config level3_tracker_free_space.toml \
  --seed 26471 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_30m/v62d_007_speedbin_velocity_coef_2x_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --command-vel-error-coef 1.2 \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_007_speedbin_velocity_coef_2x_30m \
  --wandb-run-id v62d_007_speedbin_velocity_coef_2x_30m_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_007_speedbin_velocity_coef_2x_30m_20260627
```

Training completed `30,015,488` steps from scratch. Steady-state throughput was
about `1.243M env steps/s`, roughly `31.2x` the PyTorch fast path.

## Eval Protocol

Generated milestone artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_30m_summary.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_30m_milestone_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_30m_milestone_eval.csv
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_30m_best_audit.json
```

Milestones were evaluated at `5M / 10M / 15M / 20M / 25M / 30M / final` with:

```text
config: level3_tracker_free_space.toml
seed: 26310
num_envs: 1024
num_steps: 32
eval_rollouts: 16
action_distribution: tanh_squashed_gaussian
command_generator_profile: speed_bin_balanced
reward_coefficients: {"vel_error_coef": 1.2}
```

## Milestone Results

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| v62c 7M default | -4.8459 | 0.6573 | 0.5214 | 0.7397 | 0.00391 | 0.000006 | -7.5365 |
| v62c 7M speed-bin | -2.1434 | 0.2095 | 0.1786 | 0.8179 | 0.00000 | 0.000034 | -3.4438 |
| v62d_004 best | -2.0530 | 0.1958 | 0.1634 | 0.7740 | 0.00000 | 0.000116 | -3.2704 |
| v62d_006 best | -2.0644 | 0.1964 | 0.1640 | 0.7789 | 0.00000 | 0.000092 | -3.2878 |
| 5M | -2.6548 | 0.2119 | 0.1813 | 0.8263 | 0.00000 | 0.000020 | -3.9703 |
| 10M | -2.7212 | 0.2190 | 0.1892 | 0.8533 | 0.00000 | 0.000037 | -4.0830 |
| 15M | -2.5724 | 0.2026 | 0.1710 | 0.7943 | 0.00000 | 0.000088 | -3.8301 |
| 20M | -2.6168 | 0.2070 | 0.1759 | 0.8109 | 0.00000 | 0.000059 | -3.9029 |
| 25M | -2.6528 | 0.2113 | 0.1807 | 0.8252 | 0.00000 | 0.000078 | -3.9657 |
| 30M | -3.1670 | 0.2596 | 0.2329 | 1.0491 | 0.00000 | 0.000456 | -4.8231 |
| final | -3.1670 | 0.2596 | 0.2329 | 1.0491 | 0.00000 | 0.000456 | -4.8231 |

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

Best checkpoint inside v62d_007:

```text
15M
lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_30m/v62d_007_speedbin_velocity_coef_2x_30m_step_015000000.pkl
```

Best metrics:

```text
reward_mean=-2.5724
command_position_error=0.2026
cross_track_error=0.1710
command_velocity_error=0.7943
done_mean=0.0
action_delta_penalty=0.0000875
balanced_score=-3.8301
```

Against v62c 7M default:

| Metric | v62c 7M default | v62d_007 15M | Change |
|---|---:|---:|---:|
| command position error | 0.6573 | 0.2026 | 69.2% better |
| cross-track error | 0.5214 | 0.1710 | 67.2% better |
| command velocity error | 0.7397 | 0.7943 | 7.4% worse |
| done mean | 0.00391 | 0.00000 | better |
| action delta | 0.000006 | 0.000088 | 13.7x worse |

Against the fair same-distribution v62c 7M speed-bin baseline:

| Metric | v62c 7M speed-bin | v62d_007 15M | Change |
|---|---:|---:|---:|
| command position error | 0.2095 | 0.2026 | 3.3% better |
| cross-track error | 0.1786 | 0.1710 | 4.2% better |
| command velocity error | 0.8179 | 0.7943 | 2.9% better |
| done mean | 0.00000 | 0.00000 | unchanged |
| action delta | 0.000034 | 0.000088 | 2.6x worse |

Against v62d_004/v62d_006 local bests, v62d_007 is worse on reward, position,
cross-track, velocity, and balanced score.

## Post-Run Audit

Best-checkpoint audit:

```text
checkpoint: v62d_007...step_015000000.pkl
checkpoint_global_step: 15007744
sample_clip_fraction: 0.0
stored_vs_env_logprob_abs_mean: 3.23e-7
action_sampling_logprob: ok
action_clipping: ok
advantage_scale: ok
reward_scale: ok
initial_std: ok
```

The audit's policy scenario reports:

```text
advantage_mean=-14.8409
advantage_std=6.0399
return_mean=-158.7531
return_std=6.0408
value_mean=-143.9122
value_std=0.00177
```

The value head remains nearly constant relative to return variation. This is
not an action-path bug, but value quality is still suspect.

## Three-Reviewer Synthesis

Subagent review packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_007_speedbin_velocity_coef_2x_30m_subagent_reviews.md
```

Reviewer synthesis:

```text
tracker_eval_metrics: no promotion. Best milestone is 15M, but velocity is
worse than v62c 7M default and worse than v62d_004/v62d_006.

tracker_wandb_ppo: PPO/action plumbing is healthy. Late KL/clip/action growth
and worse velocity/reward mean do not continue v62d_007.

tracker_structure_research: switch back to Family C generator velocity
distribution. Do not add another blunt reward coefficient combination.
```

## Decision

Do not promote `v62d_007`. Keep the current formal tracker frontier as:

```text
v62c_tanh_squashed_gaussian_10m_step_007340032.pkl
```

Do not continue this candidate to 60M. Do not use the final checkpoint.

Next candidate:

```text
v62d_008_velocity_contrast_constant_speed_generator
```

Rationale:

```text
The combination of speed-bin generator and velocity coefficient does not solve
velocity obedience. The next single knob should reshape the generator's
velocity-contrast distribution: longer constant-speed windows and paired
low/medium/high speed variants on similar geometry, while preserving brake
ramps and low-speed-through behavior.
```

Because this changes generator semantics, v62d_008 requires builder/checker
support before 30M training.
