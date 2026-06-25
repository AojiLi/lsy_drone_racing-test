# v55 Line Tracking Attempt002 Analysis

Date: 2026-06-25

Stage: `line_tracking`

Run: `v55_tracker_line_tracking_terminal_hold_position_attempt002`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/xfjrtjhi`

## Result

Attempt002 passed the `line_tracking` qualification gate after the terminal
hold semantic fix and a 2M position-focused fine-tune.

| Checkpoint | Success | Crash | Mean cross-track | P90 cross-track | Mean speed error | Action delta | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `500k` | `100%` | `0%` | `0.0767m` | `0.1952m` | `0.0657m/s` | `0.0117` | pass |
| `1M` | `100%` | `0%` | `0.0643m` | `0.1872m` | `0.0666m/s` | `0.0123` | pass |
| `1.5M` | `100%` | `0%` | `0.0737m` | `0.2030m` | `0.0659m/s` | `0.0120` | pass |
| `final` | `100%` | `0%` | `0.0765m` | `0.1943m` | `0.0722m/s` | `0.0121` | pass |

Selected checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/line_tracking/v55_tracker_line_tracking_terminal_hold_position_attempt002_final.ckpt
```

Metrics JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_line_tracking_terminal_hold_position_attempt002_final_metrics.json
```

## Gate Check

The official `line_tracking` gate checker passed with `hover`, `point_hold`,
`point_reach`, and `brake_to_point` supplied as prerequisite-passed stages:

```text
success_rate: 1.0 >= 0.9
crash_rate: 0.0 <= 0.05
mean_cross_track_error_m: 0.07652631402015686 <= 0.12
p90_cross_track_error_m: 0.19432517886161804 <= 0.22
mean_speed_error_mps: 0.0721852257847786 <= 0.18
mean_action_delta_l2: 0.012063540518283844 <= 0.28
```

Next stage unlocked:

```text
heading_tracking
```

## Interpretation

The terminal-hold semantic fix removed the contradictory speed target at the
end of the line. A small position/progress fine-tune then brought p90
cross-track error under the gate while preserving speed tracking and smooth
actions.

The tracker has now passed the first true path-following exam. The next stage
checks whether it can align and maintain desired heading.

## Decision Input

Record `line_tracking` as passed, set current stage to `heading_tracking`, and
use the passing `line_tracking` checkpoint as the preferred initialization for
the next stage.
