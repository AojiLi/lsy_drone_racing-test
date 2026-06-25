# v55 Point Reach Attempt001 Analysis

Date: 2026-06-25

Stage: `point_reach`

Run: `v55_tracker_point_reach_from_point_hold_attempt001`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/cw4t7qyl`

## Result

Attempt001 passed the `point_reach` qualification gate when initialized from
the passing `point_hold` checkpoint.

| Checkpoint | Success | Crash | Mean final error | P90 final error | Overshoot | Time to target | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `1M` | `100%` | `0%` | `0.0142m` | `0.0146m` | `0.0000m` | `1.621s` | pass |
| `2M` | `100%` | `0%` | `0.0127m` | `0.0131m` | `0.0000m` | `1.598s` | pass |
| `3M` | `100%` | `0%` | `0.0044m` | `0.0050m` | `0.0000m` | `1.603s` | pass |
| `final` | `100%` | `0%` | `0.0229m` | `0.0231m` | `0.0006m` | `1.509s` | pass |

Selected checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/point_reach/v55_tracker_point_reach_from_point_hold_attempt001_final.ckpt
```

Metrics JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_point_reach_from_point_hold_attempt001_final_metrics.json
```

## Gate Check

The official `point_reach` gate checker passed with `hover` and `point_hold`
supplied as prerequisite-passed stages:

```text
success_rate: 1.0 >= 0.9
crash_rate: 0.0 <= 0.05
mean_final_position_error_m: 0.02291424199938774 <= 0.18
p90_final_position_error_m: 0.023098517209291458 <= 0.3
mean_overshoot_m: 0.0005792942829430103 <= 0.2
mean_time_to_target_s: 1.5090000629425049 <= 3.5
```

Next stage unlocked:

```text
brake_to_point
```

## Interpretation

The point tracker now reliably travels from one point to another without crash
or meaningful overshoot. All saved milestones passed, and the final checkpoint
was selected because it reached the target fastest while staying comfortably
inside all error and overshoot gates.

This stage does not yet prove deliberate braking under the stricter
`brake_to_point` gate, where terminal speed and overshoot are the central
criteria.

## Decision Input

Record `point_reach` as passed, set current stage to `brake_to_point`, and use
the passing `point_reach` checkpoint as the preferred initialization for the
next stage.
