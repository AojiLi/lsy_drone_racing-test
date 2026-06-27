# v62d_006 Speed-Bin Long-Rollout 256x128 30M Analysis

Date: 2026-06-27

## Purpose

Evaluate candidate `v62d_006_speedbin_longrollout_256x128_30m` in the high-budget
generic reference-tracker search.

This candidate tested one PPO stabilizer knob:

```text
rollout geometry: 1024 envs x 32 steps -> 256 envs x 128 steps
```

The batch size stayed `32768` samples/update, but the temporal rollout window
expanded from about `0.64s` to about `2.56s`. The hypothesis was that longer
rollout credit might help approach deceleration, hold/brake settling,
low-speed-through continuation, and recover-speed transitions.

No reward semantics, actor observation layout, action distribution, or track
config was changed.

## Training Command

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_006_speedbin_longrollout_256x128_30m \
  --config level3_tracker_free_space.toml \
  --seed 26461 \
  --num-envs 256 \
  --num-steps 128 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_30m/v62d_006_speedbin_longrollout_256x128_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_006_speedbin_longrollout_256x128_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_006_speedbin_longrollout_256x128_30m \
  --wandb-run-id v62d_006_speedbin_longrollout_256x128_30m_20260627 \
  --jax-device gpu
```

W&B:

```text
https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v62d_006_speedbin_longrollout_256x128_30m_20260627
```

Training completed `30,015,488` steps from scratch. Steady-state throughput was
about `416,751 env steps/s`, roughly `10.47x` the PyTorch fast path.

## Eval Protocol

Generated milestone artifacts, intentionally not committed:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_006_speedbin_longrollout_256x128_30m_milestone_eval.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_006_speedbin_longrollout_256x128_30m_milestone_eval.csv
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_006_speedbin_longrollout_256x128_30m_best_audit.json
```

Milestones were evaluated at `5M / 10M / 15M / 20M / 25M / 30M / final` with:

```text
config: level3_tracker_free_space.toml
seed: 26310
num_envs: 1024
num_steps: 32
eval rollouts: 16
action_distribution: tanh_squashed_gaussian
command_generator_profile: speed_bin_balanced
reward_coefficients: {}
```

This is the same comparable tracker-eval protocol used by v62d_004 and
v62d_005.

## Milestone Results

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| v62c 7M default | -4.8459 | 0.6573 | 0.5214 | 0.7397 | 0.00391 | 0.000006 | -7.5365 |
| v62c 7M speed-bin | -2.1434 | 0.2095 | 0.1786 | 0.8179 | 0.00000 | 0.000034 | -3.4438 |
| v62d_004 5M | -2.0530 | 0.1958 | 0.1634 | 0.7740 | 0.00000 | 0.000116 | -3.2704 |
| v62d_005 15M | -2.5289 | 0.2022 | 0.1725 | 0.9929 | 0.00108 | 0.011608 | -3.9707 |
| 5M | -2.1458 | 0.2101 | 0.1793 | 0.8196 | 0.00000 | 0.000020 | -3.4497 |
| 10M | -2.1242 | 0.2063 | 0.1750 | 0.8079 | 0.00000 | 0.000051 | -3.4053 |
| 15M | -2.1781 | 0.2140 | 0.1837 | 0.8359 | 0.00000 | 0.000027 | -3.5086 |
| 20M | -2.0644 | 0.1964 | 0.1640 | 0.7789 | 0.00000 | 0.000092 | -3.2878 |
| 25M | -2.1697 | 0.2135 | 0.1830 | 0.8319 | 0.00000 | 0.000059 | -3.4952 |
| 30M | -2.5122 | 0.2608 | 0.2345 | 1.0318 | 0.00000 | 0.000174 | -4.1597 |
| final | -2.5122 | 0.2608 | 0.2345 | 1.0318 | 0.00000 | 0.000174 | -4.1597 |

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

Best checkpoint inside v62d_006:

```text
20M
lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_30m/v62d_006_speedbin_longrollout_256x128_30m_step_020000000.pkl
```

Against the standing v62c 7M default frontier:

| Metric | v62c 7M default | v62d_006 20M | Change |
|---|---:|---:|---:|
| command position error | 0.6573 | 0.1964 | 70.1% better |
| cross-track error | 0.5214 | 0.1640 | 68.5% better |
| command velocity error | 0.7397 | 0.7789 | 5.3% worse |
| done mean | 0.00391 | 0.00000 | better |
| action delta | 0.000006 | 0.000092 | 14.4x worse |

Against the fair same-distribution v62c 7M speed-bin baseline:

| Metric | v62c 7M speed-bin | v62d_006 20M | Change |
|---|---:|---:|---:|
| command position error | 0.2095 | 0.1964 | 6.2% better |
| cross-track error | 0.1786 | 0.1640 | 8.2% better |
| command velocity error | 0.8179 | 0.7789 | 4.8% better |
| done mean | 0.00000 | 0.00000 | tied |
| action delta | 0.000034 | 0.000092 | 2.7x worse |

Against the previous speed-bin best:

| Metric | v62d_004 5M | v62d_006 20M | Change |
|---|---:|---:|---:|
| command position error | 0.1958 | 0.1964 | 0.3% worse |
| cross-track error | 0.1634 | 0.1640 | 0.4% worse |
| command velocity error | 0.7740 | 0.7789 | 0.6% worse |
| done mean | 0.00000 | 0.00000 | tied |
| action delta | 0.000116 | 0.000092 | 20.7% better |
| balanced score | -3.2704 | -3.2878 | slightly worse |

The long-rollout knob did not produce a material promotion. It is much better
than v62d_005, but it does not beat v62d_004 and it does not improve velocity
by the required `10%-15%` over the standing v62c 7M baseline.

## Post-Run Audit

Best checkpoint audit:

```text
checkpoint: v62d_006...step_020000000.pkl
checkpoint_global_step: 20,021,248
sample_clip_fraction: 0.0
stored_vs_env_logprob_abs_mean: 3.20e-7
action_clipping: ok
action_sampling_logprob: ok
advantage_scale: ok
reward_scale: ok
initial_std: ok
```

The action/logprob path is clean. The best checkpoint's behavior gap is not an
action-distribution bug.

However, the value head remains weak:

```text
best-audit value std: 0.0015
best-audit return std: 3.4640
best-audit advantage mean/std: -4.899 / 3.464
```

The final training batch also shows late update pressure:

```text
final approx_kl: 0.0468
final clip_fraction: 0.3330
final explained_variance: 0.1739
final rollout velocity error: 0.9927
final rollout done_mean: 0.0240
```

The final checkpoint is worse than the 20M milestone, so do not use final.

## Three-Reviewer Synthesis

The three read-only reviewers agreed:

```text
tracker_eval_metrics: do not promote; 20M is best but does not beat v62d_004.
tracker_wandb_ppo: do not promote or continue to 60M; action path is clean, but late PPO pressure and final drift are visible.
tracker_structure_research: launch a best-of-family combination next: speed_bin_balanced + command_vel_error_coef=1.2, back on 1024x32.
```

## Decision

Do not promote `v62d_006_speedbin_longrollout_256x128_30m`.

Reasons:

```text
velocity is 5.3% worse than the standing v62c 7M default baseline
velocity is 0.6% worse than v62d_004 5M
balanced score is slightly worse than v62d_004 5M
final/30M drifts down sharply from 20M
long rollout is about 3x slower than 1024x32
the run does not meet the 10%-15% velocity promotion threshold
```

The useful evidence is that `256x128` is semantically valid and action/logprob
clean, but it is not the next best base.

## Next Recommendation

Launch a Family E best-of-family combination after support/checker:

```text
v62d_007_speedbin_velocity_coef_2x_30m
command_generator_profile=speed_bin_balanced
command_vel_error_coef=1.2
num_envs=1024
num_steps=32
value_target_scale=1.0
num_minibatches=4
update_epochs=1
action_distribution=tanh_squashed_gaussian
train from scratch
```

Rationale:

```text
v62d_004 gave the best generator/spatial signal.
v62d_003 gave the only direct velocity-coefficient improvement signal, though too weak alone.
v62d_006 showed longer rollout does not solve velocity obedience.
```

Keep all hard boundaries: clean command-v3 observation, tanh-squashed Gaussian,
no gate/aperture/race/finish/stage reward, no gate/obstacle/planner-phase actor
inputs, and unchanged `config/level3.toml`.
