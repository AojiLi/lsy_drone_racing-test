# v55 Point Hold Attempt001 Analysis

Date: 2026-06-25

Stage: `point_hold`

Run: `v55_tracker_point_hold_from_hover_attempt001`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/8xq9qj5w`

## Result

Attempt001 passed the `point_hold` qualification gate when initialized from the
passing hover checkpoint.

| Checkpoint | Success | Crash | Mean final error | P90 final error | Terminal speed | Overshoot | Hold ratio | Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `500k` | `100%` | `0%` | `0.0138m` | `0.0154m` | `0.0675m/s` | `0.0007m` | `0.8515` | pass |
| `1M` | `100%` | `0%` | `0.0490m` | `0.0494m` | `0.0006m/s` | `0.0000m` | `0.8511` | pass |
| `1.5M` | `100%` | `0%` | `0.0063m` | `0.0085m` | `0.0334m/s` | `0.0006m` | `0.8685` | pass |
| `final` | `100%` | `0%` | `0.0185m` | `0.0192m` | `0.0003m/s` | `0.0000m` | `0.8661` | pass |

Selected checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/point_hold/v55_tracker_point_hold_from_hover_attempt001_final.ckpt
```

Metrics JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_point_hold_from_hover_attempt001_final_metrics.json
```

## Gate Check

The official `point_hold` gate checker passed with `hover` supplied as a
prerequisite-passed stage:

```text
success_rate: 1.0 >= 0.9
crash_rate: 0.0 <= 0.03
mean_final_position_error_m: 0.018528476357460022 <= 0.15
p90_final_position_error_m: 0.019227204844355583 <= 0.25
mean_terminal_speed_mps: 0.00030724474345333874 <= 0.2
mean_overshoot_m: 0.0 <= 0.16
hold_time_ratio: 0.8660999536514282 >= 0.6
```

Next stage unlocked:

```text
point_reach
```

## Interpretation

The hover PD-warmstarted tracker transferred cleanly to `point_hold`. Unlike
hover attempt004, no milestone-specific tradeoff was needed: every saved
checkpoint passed the stage gate. The final checkpoint is selected because it
has very low terminal speed, zero mean overshoot, and strong hold ratio.

This proves the tracker can reach a point and stay near it. It still does not
prove longer travel, braking after approach, line tracking, or curved
trajectory tracking.

## Decision Input

Record `point_hold` as passed, set current stage to `point_reach`, and use the
passing `point_hold` checkpoint as the preferred initialization for the next
stage.
