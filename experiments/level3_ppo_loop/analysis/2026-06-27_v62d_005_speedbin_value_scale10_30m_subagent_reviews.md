# v62d_005 Subagent Reviews

Date: 2026-06-27

## tracker_eval_metrics

Verdict: do not promote `v62d_005`. Best milestone is `15M`:

```text
lsy_drone_racing/control/checkpoints/v62d_005_speedbin_value_scale10_30m/v62d_005_speedbin_value_scale10_30m_step_015000000.pkl
```

Primary evidence:

| checkpoint | reward | pos err | cross-track | vel err | done | action delta | balanced |
|---|---:|---:|---:|---:|---:|---:|---:|
| 5M | -2.5342 | 0.2629 | 0.2369 | 1.0448 | 0.00003 | 0.000132 | -4.1994 |
| 10M | -4.7239 | 0.2971 | 0.2658 | 1.6365 | 0.00524 | 0.011770 | -7.0201 |
| 15M | -2.5289 | 0.2022 | 0.1725 | 0.9929 | 0.00108 | 0.011608 | -3.9707 |
| 20M | -5.7899 | 0.2519 | 0.2308 | 1.1951 | 0.01317 | 0.014194 | -7.6963 |
| 25M | -9.0211 | 0.2494 | 0.2333 | 1.3116 | 0.02606 | 0.017564 | -11.1494 |
| 30M/final | -6.9934 | 0.2207 | 0.2067 | 1.1597 | 0.01936 | 0.013310 | -8.8348 |

Against the standing v62c 7M default baseline, position and cross-track improve
strongly, but velocity is `34.2%` worse and action delta is `1818x` worse.

Against the v62c 7M speed-bin baseline, v62d_005 15M is slightly better on
position and cross-track, but velocity is `21.4%` worse, done rate regresses
from `0.0` to `0.00108`, and action delta is about `341x` worse.

Against v62d_004 5M, v62d_005 15M is worse on every important promotion metric:
position `3.2%` worse, cross-track `5.6%` worse, velocity `28.3%` worse, action
delta `99.8x` worse, and balanced score worse by about `0.70`.

Failure modes:

```text
best checkpoint is 15M, not final
10M and 20M-30M/final show instability and done-rate drift
velocity obedience is much worse than baseline and prior speed-bin best
action smoothness is the main behavioral regression
```

## tracker_wandb_ppo

Verdict: value scaling improved critic diagnostics, but the controller behavior
is not healthy enough to promote.

Value/critic health improved:

```text
final value_loss = 0.0603
last-10% mean value_loss ~= 0.0725
final explained_variance = 0.731
last-10% mean explained_variance ~= 0.728
values_scaled_mean = -25.782
value_targets_mean = -25.795
```

Advantage scale is no longer the main blocker:

```text
best audit advantage mean/std = -0.638 / 3.91
final W&B advantage mean/std = -0.126 / 3.49
```

PPO update pressure is mixed but not an obvious blow-up:

```text
final approx_kl = 0.0139
mean approx_kl ~= 0.0145
final clip_fraction = 0.204
mean clip_fraction ~= 0.176
clip_fraction spikes up to about 0.512
```

Action/logprob path:

```text
rollout_action_clip_fraction = 0.0
rollout_action_any_dim_clipped_fraction = 0.0
final stored-vs-env logprob consistency ~= 2.46e-6
best audit stored_vs_env_logprob_abs_mean = 1.76e-6
best audit action_sampling_logprob = bad
```

The strict logprob verdict is borderline numeric, but the behavior metrics make
it non-promotable anyway.

Primary behavioral failure:

```text
eval action_abs_mean: 0.016 initial -> 0.579 final
15M action_delta_penalty: 0.0116
final action_delta_penalty: 0.0133
final velocity error: 1.2135
final done mean: 0.0296
```

Learning signal is narrow:

```text
position improves: 1.121 -> 0.268
cross-track improves: 0.893 -> 0.251
reward worsens: -5.72 -> -9.81
velocity worsens: 0.459 -> 1.214
done rate worsens: 0.0022 -> 0.0296
```

Recommendation: reward tuning should wait. The current issue is aggressive
position/cross-track chasing with poor velocity obedience and high action
delta, not a missing gate or reward semantic.

## tracker_structure_research

Recommendation: switch away from Family A value/return scaling.

Reasoning:

```text
v62d_001, v62d_002, and v62d_005 now show that critic target scaling can improve
value diagnostics without improving generic command obedience.
v62d_005 also amplified action magnitude and action-delta instability.
v62d_004 remains the most useful local signal because speed_bin_balanced gives
good spatial tracking and zero done rate at early checkpoints.
```

Next candidate:

```text
v62d_006_speedbin_longrollout_256x128_30m
```

Family:

```text
D_PPO_stabilizer
```

Single changed knob:

```text
rollout geometry: 1024 envs x 32 steps -> 256 envs x 128 steps
```

Keep:

```text
command_generator_profile=speed_bin_balanced
value_target_scale=1.0
command_vel_error_coef=default
action_distribution=tanh_squashed_gaussian
observation_layout=level3_reference_tracker_command_v3
no gate/aperture/race/finish/stage rewards
```

Builder/checker support is required before 30M training because rollout geometry
changes training semantics. The checker should verify unchanged
`config/level3.toml`, unchanged `config/level3_tracker_free_space.toml`,
correct `256x128` metadata, no reward/observation/action-distribution drift,
and a small smoke/audit pass.

