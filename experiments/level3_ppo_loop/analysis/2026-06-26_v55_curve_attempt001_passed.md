# v55 Curve Tracking Attempt001 Analysis

Date: 2026-06-26

Stage: `curve_tracking`

Run: `v55_tracker_curve_from_l_shape_attempt001`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/wnqiezlv`

## Result

Attempt001 passed the `curve_tracking` qualification gate. All evaluated
milestone checkpoints passed. The best promotion checkpoint is the 9M
milestone because it keeps p90 cross-track error, oscillation, and action delta
low while improving mean cross-track error relative to the earliest checkpoint.

Selected checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/curve_tracking/v55_tracker_curve_from_l_shape_attempt001_step_034958400.ckpt
```

Selected metrics JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_curve_from_l_shape_attempt001_step9m_metrics.json
```

## Milestone Summary

| Checkpoint | Path completion | Crash | Mean cross-track | P90 cross-track | Oscillation | Action delta | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `1M` | `100%` | `0%` | `0.1114m` | `0.2007m` | `0.0073` | `0.0087` | pass |
| `2M` | `100%` | `0%` | `0.0554m` | `0.2190m` | `0.0841` | `0.0328` | pass |
| `3M` | `100%` | `0%` | `0.0677m` | `0.2513m` | `0.1567` | `0.0682` | pass |
| `4M` | `100%` | `0%` | `0.0783m` | `0.2699m` | `0.1792` | `0.0680` | pass |
| `5M` | `100%` | `0%` | `0.0849m` | `0.2830m` | `0.1939` | `0.0631` | pass |
| `6M` | `100%` | `0%` | `0.0876m` | `0.2883m` | `0.0562` | `0.0239` | pass |
| `7M` | `100%` | `0%` | `0.0848m` | `0.2622m` | `0.0185` | `0.0122` | pass |
| `8M` | `100%` | `0%` | `0.0837m` | `0.2203m` | `0.0113` | `0.0104` | pass |
| `9M` | `100%` | `0%` | `0.0928m` | `0.2037m` | `0.0106` | `0.0099` | pass |
| `final` | `100%` | `0%` | `0.0519m` | `0.2117m` | `0.1225` | `0.0574` | pass |

## Gate Check

The official `curve_tracking` gate checker passed for the selected 9M
checkpoint with prerequisite history through `l_shape_tracking`.

Required metrics:

```text
checkpoint_backed = true
all_finite = true
path_completion_rate = 1.0 >= 0.8
crash_rate = 0.0 <= 0.07
mean_cross_track_error_m = 0.09281318634748459 <= 0.18
p90_cross_track_error_m = 0.2037346214056015 <= 0.35
oscillation_score = 0.010572141967713833 <= 0.35
mean_action_delta_l2 = 0.009870258159935474 <= 0.35
```

Next stage unlocked:

```text
zigzag_or_lemniscate_tracking
```

## Interpretation

The tracker can now follow a smooth curved trajectory without crashing,
oscillating heavily, or producing aggressive action changes. The final
checkpoint has the lowest mean cross-track error, but oscillation and action
delta are higher. The 9M checkpoint is a better balanced promotion point.

## Decision Input

Record `curve_tracking` as passed, set current stage to
`zigzag_or_lemniscate_tracking`, and use the selected 9M checkpoint as the
preferred initialization for the next tracker stage.
