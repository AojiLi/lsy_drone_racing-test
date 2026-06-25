# v55 Line Tracking Attempt001 Analysis

Date: 2026-06-25

Stage: `line_tracking`

Run: `v55_tracker_line_tracking_from_brake_attempt001`

W&B: `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/vdqdpog0`

## Result

Attempt001 did not pass the `line_tracking` qualification gate.

| Checkpoint | Success | Crash | Mean cross-track | P90 cross-track | Mean speed error | Action delta |
|---|---:|---:|---:|---:|---:|---:|
| `1M` | `100%` | `0%` | `0.1045m` | `0.2897m` | `0.3167m/s` | `0.0126` |
| `2M` | `100%` | `0%` | `0.1014m` | `0.2728m` | `0.3115m/s` | `0.0104` |
| `3M` | `100%` | `0%` | `0.1233m` | `0.2586m` | `0.3189m/s` | `0.0099` |
| `4M` | `100%` | `0%` | `0.1083m` | `0.2285m` | `0.3190m/s` | `0.0098` |
| `final` | `100%` | `0%` | `0.0725m` | `0.2287m` | `0.3113m/s` | `0.0100` |

Best diagnostic checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/line_tracking/v55_tracker_line_tracking_from_brake_attempt001_final.ckpt
```

Gate failures:

```text
p90_cross_track_error_m = 0.22865745425224304 > 0.22
mean_speed_error_mps = 0.3112734258174896 > 0.18
```

## Three-Review Synthesis

- `tracker_eval_metrics`: the policy is safe and completes the path, but speed
  tracking is systematically too slow. The p90 cross-track miss is edge-level;
  speed error is the real blocker.
- `tracker_wandb_ppo`: PPO is not obviously unstable. KL/clip are controlled,
  eval is finite, and action smoothness is strong. The learned deterministic
  policy is conservative and slow.
- `tracker_structure_research`: the line task has a semantic inconsistency:
  the 0.9m path at 0.38m/s reaches the endpoint after about 2.4s, but the
  evaluator runs 10s. The reference point clamps to the endpoint while
  `desired_speed` remains nonzero, so the policy is asked to hold position and
  keep moving at the same time.

## Main-Agent Diagnosis

Do not unlock `heading_tracking`.

Do not run another identical 5M chunk before fixing the line reference
semantics. The primary failure is not crash, not basic path following, and not
obvious PPO instability. It is a mismatch between the terminal path phase and
the speed-error metric.

## Decision Input

The next action should be a semantic builder/checker fix:

```text
When a finite polyline reference has reached its terminal point, switch to a
terminal hold reference with desired_speed = 0 and desired_velocity = 0.
```

After checker passes, re-evaluate the existing attempt001 checkpoint under the
fixed semantics. If it still fails active line-speed tracking, then launch a
new `line_tracking` attempt with stronger velocity/path-progress pressure.
