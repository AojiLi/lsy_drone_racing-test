# v62d_005 Speed-Bin Value Scale 10 30M Analysis

Date: 2026-06-27

## Purpose

Evaluate candidate `v62d_005_speedbin_value_scale10_30m` in the high-budget
generic reference-tracker search.

Hypothesis:

```text
Keep the useful speed_bin_balanced command distribution from v62d_004, but use
a narrower critic target scale to improve value/return health and reduce the
late drift seen after the v62d_004 5M peak.
```

This is a bottom-tracker free-space command-following run, not a Level3 hard
eval.

## Training Command

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_005_speedbin_value_scale10_30m \
  --config level3_tracker_free_space.toml \
  --seed 26451 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_005_speedbin_value_scale10_30m/v62d_005_speedbin_value_scale10_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_005_speedbin_value_scale10_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --value-target-scale 10.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_005_speedbin_value_scale10_30m \
  --wandb-run-id v62d_005_speedbin_value_scale10_30m_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_005_speedbin_value_scale10_30m_20260627
```

Training completed `30,015,488` steps from scratch. Steady-state throughput was
about `1.243M env steps/s`, roughly `31.2x` the PyTorch fast path.

## Eval Protocol

Generated milestone artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_005_speedbin_value_scale10_30m_milestone_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_005_speedbin_value_scale10_30m_milestone_eval.csv
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_005_speedbin_value_scale10_30m_best_audit.json
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

## Milestone Results

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| v62c 7M default | -4.8459 | 0.6573 | 0.5214 | 0.7397 | 0.00391 | 0.000006 | -7.5365 |
| v62c 7M speed-bin | -2.1434 | 0.2095 | 0.1786 | 0.8179 | 0.00000 | 0.000034 | -3.4438 |
| v62d_004 5M | -2.0530 | 0.1958 | 0.1634 | 0.7740 | 0.00000 | 0.000116 | -3.2704 |
| 5M | -2.5342 | 0.2629 | 0.2369 | 1.0448 | 0.00003 | 0.000132 | -4.1994 |
| 10M | -4.7239 | 0.2971 | 0.2658 | 1.6365 | 0.00524 | 0.011770 | -7.0201 |
| 15M | -2.5289 | 0.2022 | 0.1725 | 0.9929 | 0.00108 | 0.011608 | -3.9707 |
| 20M | -5.7899 | 0.2519 | 0.2308 | 1.1951 | 0.01317 | 0.014194 | -7.6963 |
| 25M | -9.0211 | 0.2494 | 0.2333 | 1.3116 | 0.02606 | 0.017564 | -11.1494 |
| 30M | -6.9934 | 0.2207 | 0.2067 | 1.1597 | 0.01936 | 0.013310 | -8.8348 |
| final | -6.9934 | 0.2207 | 0.2067 | 1.1597 | 0.01936 | 0.013310 | -8.8348 |

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

Best checkpoint inside v62d_005:

```text
15M
lsy_drone_racing/control/checkpoints/v62d_005_speedbin_value_scale10_30m/v62d_005_speedbin_value_scale10_30m_step_015000000.pkl
```

Against the standing v62c 7M default frontier:

| Metric | v62c 7M default | v62d_005 15M | Change |
|---|---:|---:|---:|
| command position error | 0.6573 | 0.2022 | 69.2% better |
| cross-track error | 0.5214 | 0.1725 | 66.9% better |
| command velocity error | 0.7397 | 0.9929 | 34.2% worse |
| done mean | 0.00391 | 0.00108 | better |
| action delta | 0.000006 | 0.011608 | 1818x worse |

Against the fair same-distribution v62c 7M speed-bin baseline:

| Metric | v62c 7M speed-bin | v62d_005 15M | Change |
|---|---:|---:|---:|
| command position error | 0.2095 | 0.2022 | 3.5% better |
| cross-track error | 0.1786 | 0.1725 | 3.4% better |
| command velocity error | 0.8179 | 0.9929 | 21.4% worse |
| done mean | 0.00000 | 0.00108 | worse |
| action delta | 0.000034 | 0.011608 | 341x worse |

Against the previous speed-bin candidate best:

| Metric | v62d_004 5M | v62d_005 15M | Change |
|---|---:|---:|---:|
| command position error | 0.1958 | 0.2022 | 3.2% worse |
| cross-track error | 0.1634 | 0.1725 | 5.6% worse |
| command velocity error | 0.7740 | 0.9929 | 28.3% worse |
| done mean | 0.00000 | 0.00108 | worse |
| action delta | 0.000116 | 0.011608 | 99.8x worse |

The candidate does not meet the promotion threshold. It improves spatial
tracking relative to the standing default baseline, but velocity obedience and
action smoothness regress too much.

## Post-Run Audit

Best checkpoint audit:

```text
checkpoint: v62d_005...step_015000000.pkl
checkpoint_global_step: 15,007,744
sample_clip_fraction: 0.0
stored_vs_env_logprob_abs_mean: 1.76e-6
action_clipping: ok
action_sampling_logprob: bad
advantage_scale: ok
reward_scale: ok
initial_std: ok
```

The `action_sampling_logprob=bad` verdict is just over the strict `1e-6`
threshold and may be partly numeric sensitivity, but it is not ignorable in a
promotion decision because the same checkpoint also has very large action
magnitude and action delta.

The useful part of v62d_005 is critic scale:

```text
final explained_variance: 0.7309
final value_loss: 0.0603
final advantages std: 3.486
final values_scaled_mean: -25.7819
final value_targets_mean: -25.7945
```

The failing part is controller behavior:

```text
final action_abs_mean: 0.5784
final rollout action_delta_penalty: 0.0219
final rollout velocity error: 1.2392
final rollout done_mean: 0.0310
```

## Three-Reviewer Synthesis

Reviewer 1, tracker eval metrics:

```text
Reject. Best milestone is 15M, but it is worse than v62d_004 5M on reward,
velocity, done rate, action delta, and balanced score. Final is not best.
```

Reviewer 2, W&B/PPO diagnostics:

```text
Value scaling helped critic/value diagnostics, but behavior is unhealthy.
Action clipping is zero and stored-vs-env logprob is near-zero, but action
magnitude/delta drift is the primary problem. Reward tuning should wait.
```

Reviewer 3, structure/research:

```text
Stop Family A value target scaling for now. v62d_001, v62d_002, and v62d_005
show that critic scaling can improve the value ledger without improving
generic command obedience. Next try a PPO stabilizer: longer rollout horizon
256 envs x 128 steps, keeping the speed-bin generator and default reward.
```

## Decision

Do not promote `v62d_005`. Keep the current tracker frontier as `v62c 7M`.

Next candidate:

```text
v62d_006_speedbin_longrollout_256x128_30m
```

Rationale:

```text
v62d_004 remains the best speed-bin signal. v62d_005 shows value scaling can
make critic diagnostics healthier but can also produce aggressive actions and
worse velocity obedience. The next single knob should be temporal credit and
rollout horizon, not another value scale or reward-number change.
```

