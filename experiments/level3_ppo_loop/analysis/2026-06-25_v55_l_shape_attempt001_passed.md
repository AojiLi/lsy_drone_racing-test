# v55 L-Shape Tracking Attempt001 Analysis

Date: 2026-06-25

Stage: `l_shape_tracking`

Run: `v55_tracker_l_shape_from_multi_point_attempt001`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/1moondkl`

## Result

Attempt001 passed the `l_shape_tracking` qualification gate. The best promotion
checkpoint is the 5M milestone because it combines the lowest p90 cross-track
error among the strong passing checkpoints with smooth actions.

Selected checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/l_shape_tracking/v55_tracker_l_shape_from_multi_point_attempt001_step_025958208.ckpt
```

Selected metrics JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_l_shape_from_multi_point_attempt001_step5m_metrics.json
```

## Milestone Summary

| Checkpoint | Corner completion | Crash | Mean cross-track | P90 cross-track | Corner overshoot | Action delta | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `1M` | `100%` | `0%` | `0.1436m` | `0.2382m` | `0.0134m` | `0.0087` | pass |
| `2M` | `100%` | `0%` | `0.1482m` | `0.2187m` | `0.0929m` | `0.0093` | pass |
| `3M` | `0%` | `0%` | `0.2104m` | `0.2945m` | `0.1201m` | `0.0079` | fail completion/mean |
| `4M` | `50%` | `0%` | `0.1770m` | `0.2509m` | `0.1579m` | `0.0085` | fail completion |
| `5M` | `100%` | `0%` | `0.1186m` | `0.2026m` | `0.0965m` | `0.0106` | pass |
| `6M` | `100%` | `0%` | `0.0969m` | `0.2165m` | `0.0712m` | `0.0150` | pass |
| `7M` | `100%` | `0%` | `0.0913m` | `0.2465m` | `0.0635m` | `0.0182` | pass |
| `final` | `100%` | `0%` | `0.0804m` | `0.2399m` | `0.0537m` | `0.0536` | pass |

## Gate Check

The official `l_shape_tracking` gate checker passed for the selected 5M
checkpoint with prerequisite history through `multi_point_reference`.

Required metrics:

```text
checkpoint_backed = true
all_finite = true
corner_completion_rate = 1.0 >= 0.8
crash_rate = 0.0 <= 0.07
mean_cross_track_error_m = 0.118613600730896 <= 0.18
p90_cross_track_error_m = 0.20258449018001556 <= 0.32
mean_corner_overshoot_m = 0.09654346853494644 <= 0.28
mean_action_delta_l2 = 0.010565461590886116 <= 0.35
```

Next stage unlocked:

```text
curve_tracking
```

## Interpretation

The tracker can now follow an L-shaped route and complete the corner without
crashing or excessive overshoot. The final checkpoint has the lowest mean
cross-track error, but action delta rises substantially. The 5M checkpoint is a
better balance for promotion because it has the lowest p90 cross-track error
and remains smooth.

## Decision Input

Record `l_shape_tracking` as passed, set current stage to `curve_tracking`, and
use the selected 5M checkpoint as the preferred initialization for the next
tracker stage.
