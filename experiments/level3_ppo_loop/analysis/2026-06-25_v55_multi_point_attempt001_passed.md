# v55 Multi-Point Reference Attempt001 Analysis

Date: 2026-06-25

Stage: `multi_point_reference`

Run: `v55_tracker_multi_point_from_heading_attempt001`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/filmeri9`

## Result

Attempt001 passed the `multi_point_reference` qualification gate. The best
promotion checkpoint is the 1M milestone because it has the lowest p90 position
error and the smoothest action changes among the passing checkpoints.

Selected checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/multi_point_reference/v55_tracker_multi_point_from_heading_attempt001_step_020957760.ckpt
```

Selected metrics JSON:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v55_multi_point_from_heading_attempt001_step1m_metrics.json
```

## Milestone Summary

| Checkpoint | Segment completion | Crash | Mean position error | P90 position error | Switch overshoot | Action delta | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| `1M` | `100%` | `0%` | `0.1784m` | `0.2786m` | `0.0046m` | `0.0091` | pass |
| `2M` | `100%` | `0%` | `0.1834m` | `0.3071m` | `0.0101m` | `0.0098` | pass |
| `3M` | `100%` | `0%` | `0.2091m` | `0.3402m` | `0.0216m` | `0.0127` | fail mean position |
| `4M` | `100%` | `0%` | `0.1713m` | `0.3290m` | `0.0153m` | `0.0135` | pass |
| `5M` | `100%` | `0%` | `0.1229m` | `0.3210m` | `0.0208m` | `0.0142` | pass |
| `6M` | `100%` | `0%` | `0.1322m` | `0.4221m` | `0.0009m` | `0.0202` | fail p90 position |
| `7M` | `100%` | `0%` | `0.1320m` | `0.3765m` | `0.0000m` | `0.0259` | fail p90 position |
| `final` | `100%` | `0%` | `0.1549m` | `0.3119m` | `0.0035m` | `0.0264` | pass |

## Gate Check

The official `multi_point_reference` gate checker passed for the selected 1M
checkpoint with prerequisite history through `heading_tracking`.

Required metrics:

```text
checkpoint_backed = true
all_finite = true
segment_completion_rate = 1.0 >= 0.85
crash_rate = 0.0 <= 0.05
mean_position_error_m = 0.1784248650074005 <= 0.2
p90_position_error_m = 0.2786217927932739 <= 0.35
mean_switch_overshoot_m = 0.004599432460963726 <= 0.25
mean_action_delta_l2 = 0.009103040210902691 <= 0.32
```

Next stage unlocked:

```text
l_shape_tracking
```

## Interpretation

The tracker can now follow multiple reference points and switch between them
without crashing or producing large action jumps. Later checkpoints improve
some average position metrics but worsen p90 position error and action delta,
so the earliest passing 1M checkpoint is the safer promotion point for the
next structural stage.

## Decision Input

Record `multi_point_reference` as passed, set current stage to
`l_shape_tracking`, and use the selected 1M checkpoint as the preferred
initialization for the next tracker stage.
