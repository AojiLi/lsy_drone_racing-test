# v62d_004 Speed-Bin Balanced Generator 30M Analysis

Date: 2026-06-27

## Purpose

Evaluate candidate `v62d_004_speed_bin_balanced_generator_30m` in the
high-budget generic reference-tracker search.

Hypothesis:

```text
Rebalancing the command generator toward explicit speed bins, longer brake
ramps, longer low-speed-through windows, and longer recover transitions will
teach velocity obedience from the reference distribution instead of a larger
scalar velocity penalty.
```

This is a bottom-tracker free-space command-following run, not a Level3 hard
eval.

## Training Command

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_004_speed_bin_balanced_generator_30m \
  --config level3_tracker_free_space.toml \
  --seed 26441 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_004_speed_bin_balanced_generator_30m/v62d_004_speed_bin_balanced_generator_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_004_speed_bin_balanced_generator_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_004_speed_bin_balanced_generator_30m \
  --wandb-run-id v62d_004_speed_bin_balanced_generator_30m_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_004_speed_bin_balanced_generator_30m_20260627
```

Training completed `30,015,488` steps from scratch. Steady-state throughput was
about `1.246M env steps/s`.

## Eval Protocol

Generated milestone artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_004_speed_bin_balanced_generator_30m_milestone_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_004_speed_bin_balanced_generator_30m_milestone_eval.csv
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_004_v62c7m_speedbin_baseline_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_004_speed_bin_balanced_generator_30m_best_audit.json
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
reward_coefficients: {}
```

Because this candidate changes the generator distribution, a separate v62c 7M
speed-bin baseline was also evaluated under the same `speed_bin_balanced`
protocol.

## Milestone Results

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| v62c 7M default | -4.8459 | 0.6573 | 0.5214 | 0.7397 | 0.00391 | 0.000006 | -7.5365 |
| v62c 7M speed-bin | -2.1434 | 0.2095 | 0.1786 | 0.8179 | 0.00000 | 0.000034 | -3.4438 |
| 5M | -2.0530 | 0.1958 | 0.1634 | 0.7740 | 0.00000 | 0.000116 | -3.2704 |
| 10M | -2.0840 | 0.2004 | 0.1685 | 0.7873 | 0.00000 | 0.000291 | -3.3286 |
| 15M | -2.1321 | 0.2066 | 0.1754 | 0.8108 | 0.00000 | 0.000261 | -3.4170 |
| 20M | -2.1671 | 0.2125 | 0.1820 | 0.8285 | 0.00000 | 0.000416 | -3.4874 |
| 25M | -2.1752 | 0.2138 | 0.1833 | 0.8323 | 0.00000 | 0.000497 | -3.5029 |
| 30M | -2.2033 | 0.2184 | 0.1886 | 0.8484 | 0.00000 | 0.000578 | -3.5605 |
| final | -2.2033 | 0.2184 | 0.1886 | 0.8484 | 0.00000 | 0.000578 | -3.5605 |

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

Best checkpoint inside v62d_004:

```text
5M
lsy_drone_racing/control/checkpoints/v62d_004_speed_bin_balanced_generator_30m/v62d_004_speed_bin_balanced_generator_30m_step_005000000.pkl
```

Against v62c 7M default:

| Metric | v62c 7M default | v62d_004 5M | Change |
|---|---:|---:|---:|
| command position error | 0.6573 | 0.1958 | 70.2% better |
| cross-track error | 0.5214 | 0.1634 | 68.7% better |
| command velocity error | 0.7397 | 0.7740 | 4.6% worse |
| done mean | 0.00391 | 0.00000 | better |
| action delta | 0.000006 | 0.000116 | 18.2x worse |

Against v62c 7M evaluated on the same speed-bin distribution:

| Metric | v62c 7M speed-bin | v62d_004 5M | Change |
|---|---:|---:|---:|
| command position error | 0.2095 | 0.1958 | 6.5% better |
| cross-track error | 0.1786 | 0.1634 | 8.5% better |
| command velocity error | 0.8179 | 0.7740 | 5.4% better |
| done mean | 0.00000 | 0.00000 | unchanged |
| action delta | 0.000034 | 0.000116 | 3.4x worse |

The candidate does not meet the promotion threshold. It does not improve
velocity by `10%-15%`, and action smoothness regresses materially.

## Post-Run Audit

Best checkpoint audit:

```text
checkpoint: v62d_004...step_005000000.pkl
checkpoint_global_step: 5,013,504
sample_clip_fraction: 0.0
stored_vs_env_logprob_abs_mean: 3.11e-7
action_sampling_logprob: ok
action_clipping: ok
advantage_scale: ok
reward_scale: ok
initial_std: ok
```

The audit's untrained initial scenario still reports `advantage_scale=large`,
but the checkpoint scenario is healthy. The action distribution and log-prob
path are not the failure.

Final training diagnostics still show the critic/value issue:

```text
value_loss: 704.21
advantages mean/std: -20.77 / 31.33
returns mean/std: -305.64 / 31.34
values mean/std: -284.87 / 0.0015
explained_variance: 0.000042
all_finite: 1.0
```

## Three-Reviewer Synthesis

Reviewer 1, tracker eval metrics:

```text
Reject v62d_004. Best milestone is 5M, but velocity improves only 5.37% under
the fair speed-bin comparison and action delta worsens. After 5M every
milestone drifts worse.
```

Reviewer 2, W&B/PPO diagnostics:

```text
Action/logprob and clipping are healthy; PPO plumbing is trustworthy. Critic
and value scale remain weak, with near-constant values late in training and
low explained variance.
```

Reviewer 3, structure/research:

```text
Do not continue generator-only tuning and do not return to blunt velocity
reward scaling. Next test value/return stabilization while keeping the useful
speed_bin_balanced generator distribution.
```

## Decision

Do not promote `v62d_004`. Keep the current tracker frontier as `v62c 7M`.

Next candidate:

```text
v62d_005_speedbin_value_scale10
```

Rationale:

```text
v62d_004 shows the speed-bin generator is useful enough to keep for the next
diagnostic, but it does not solve velocity obedience or late drift. The next
single pressure point should be value/return stabilization, not another
generator-only tweak or another blunt velocity reward coefficient change.
```
