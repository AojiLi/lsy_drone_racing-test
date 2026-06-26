# v55 Analysis: GeometricSlowGatePlanner Support

## What Changed

The Level3 native reference tracker now uses `GeometricSlowGatePlanner` for
`task="level3"` reference generation.

The planner lives in:

```text
lsy_drone_racing/control/level3_reference_tracker.py
```

It produces:

```text
current reference point
next reference point
lookahead reference point
desired speed
desired heading through existing ReferenceFrame construction
```

It does not produce roll/pitch/yaw/thrust. The PPO tracker still produces the
action.

## Planner Semantics

The planner is a deterministic gate-frame state machine:

```text
cruise
slowdown
align
cross
recover
```

It remembers the current phase and only advances forward within a gate. When
the environment advances `target_gate`, the planner resets for the next gate.
This is intended to avoid phase flicker near the gate plane.

The generated local reference horizon is conservative:

```text
pre-gate far point
pre-gate slowdown point
pre-gate align point
aperture point
post-gate point
recovery point
```

The planner also applies a simple visible-obstacle rule: if an obstacle is close
to the current local segment, it offsets the reference Y/Z within a bounded
margin. This is a first safety heuristic, not a full obstacle planner.

## Why This Is The Right First Smoke

MPPI would add many moving parts at once: dynamics rollout quality, sampling
budget, cost design, control smoothing, terminal cost, and interaction with the
PPO tracker. The current uncertainty is simpler:

```text
Can the qualified tracker follow conservative gate-frame references on Level3?
```

A deterministic planner makes failures easier to interpret:

- if references are bad, fix planner geometry;
- if references are good but tracking is poor, improve tracker curriculum;
- if phase switches are wrong, fix hysteresis/state transitions;
- if obstacle offsets are wrong, improve the waypoint heuristic.

## Validation Summary

Checks run:

```text
tracker/env/stage tests: 21 passed
ruff on changed Python files: passed
untrained controller micro smoke: all_finite=true
checkpoint-backed controller micro smoke: all_finite=true, checkpoint_backed=true
config/level3.toml diff: clean
```

The smoke output paths were:

```text
/tmp/v55_geometric_slow_gate_planner_smoke.json
/tmp/v55_geometric_slow_gate_planner_checkpoint_smoke.json
```

The checkpoint-backed micro smoke used:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
```

The micro smoke had finite actions but was too short to evaluate Level3
capability. The required next evidence is the full `planner_integration_smoke`
gate on seeds `101-120`.
