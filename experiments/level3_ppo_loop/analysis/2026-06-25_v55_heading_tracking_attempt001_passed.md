# v55 Heading Tracking Attempt001 Analysis

Date: 2026-06-25

Stage: `heading_tracking`

Run: `v55_tracker_heading_tracking_from_line_attempt001`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/451gfcx3`

## Result

Attempt001 passed the `heading_tracking` qualification gate. The best
checkpoint is the 2M milestone because it has the lowest held-out heading error
while preserving zero crashes and very smooth actions.

Selected checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/heading_tracking/v55_tracker_heading_tracking_from_line_attempt001_step_019956864.ckpt
```

Selected metrics JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_heading_tracking_from_line_attempt001_step2m_metrics.json
```

## Milestone Summary

| Checkpoint | Success | Crash | Mean heading error | P90 heading error | Mean yaw rate | Action delta | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `1M` | `100%` | `0%` | `0.1658rad` | `0.1733rad` | `0.0000` | `0.0078` | pass |
| `2M` | `100%` | `0%` | `0.1475rad` | `0.1534rad` | `0.0000` | `0.0077` | pass |
| `3M` | `100%` | `0%` | `0.1797rad` | `0.1990rad` | `0.0000` | `0.0079` | pass |
| `final` | `100%` | `0%` | `0.2442rad` | `0.2731rad` | `0.0000` | `0.0091` | pass |

## Gate Check

The official `heading_tracking` gate checker passed for the selected 2M
checkpoint with prerequisite history through `line_tracking`.

Required metrics:

```text
checkpoint_backed = true
all_finite = true
success_rate = 1.0 >= 0.9
crash_rate = 0.0 <= 0.05
mean_heading_error_rad = 0.1475260853767395 <= 0.25
p90_heading_error_rad = 0.1533883810043335 <= 0.45
mean_yaw_rate_abs = 0.0 <= 1.2
mean_action_delta_l2 = 0.007741902954876423 <= 0.28
```

Next stage unlocked:

```text
multi_point_reference
```

## Interpretation

The tracker can now align to desired heading in the free-space tracker task
without introducing crashes or aggressive action changes. The final checkpoint
also passes, but heading error drifts closer to the gate threshold, so the 2M
checkpoint is the safer promotion point.

## Decision Input

Record `heading_tracking` as passed, set current stage to
`multi_point_reference`, and use the selected 2M checkpoint as the preferred
initialization for the next tracker stage.
