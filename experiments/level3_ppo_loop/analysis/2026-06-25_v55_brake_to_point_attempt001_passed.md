# v55 Brake To Point Attempt001 Analysis

Date: 2026-06-25

Stage: `brake_to_point`

Run: `v55_tracker_brake_to_point_from_point_reach_attempt001`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/gthid6v4`

## Result

Attempt001 passed the `brake_to_point` qualification gate when initialized
from the passing `point_reach` checkpoint.

| Checkpoint | Brake success | Crash | Terminal speed | P90 terminal speed | Overshoot | P90 overshoot | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `1M` | `100%` | `0%` | `0.0004m/s` | `0.0006m/s` | `0.0000m` | `0.0000m` | pass |
| `2M` | `100%` | `0%` | `0.0003m/s` | `0.0005m/s` | `0.0000m` | `0.0000m` | pass |
| `3M` | `100%` | `0%` | `0.0003m/s` | `0.0005m/s` | `0.0000m` | `0.0000m` | pass |
| `final` | `100%` | `0%` | `0.0008m/s` | `0.0012m/s` | `0.0000m` | `0.0000m` | pass |

Selected checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/brake_to_point/v55_tracker_brake_to_point_from_point_reach_attempt001_final.ckpt
```

Metrics JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_brake_to_point_from_point_reach_attempt001_final_metrics.json
```

## Gate Check

The official `brake_to_point` gate checker passed with `hover`, `point_hold`,
and `point_reach` supplied as prerequisite-passed stages:

```text
brake_success_rate: 1.0 >= 0.85
crash_rate: 0.0 <= 0.05
mean_terminal_speed_mps: 0.0007754218531772494 <= 0.18
p90_terminal_speed_mps: 0.0011556519893929362 <= 0.3
mean_overshoot_m: 0.0 <= 0.18
p90_overshoot_m: 0.0 <= 0.32
```

Next stage unlocked:

```text
line_tracking
```

## Interpretation

The tracker now demonstrates deliberate braking at the target. This is a
critical capability for the later planner-driven Level3 lane because the upper
planner will need the drone to slow down near gates and visible obstacles.

The next stage changes the exam from point-wise braking to following a short
straight trajectory with desired speed and low cross-track error.

## Decision Input

Record `brake_to_point` as passed, set current stage to `line_tracking`, and
use the passing `brake_to_point` checkpoint as the preferred initialization for
the next stage.
