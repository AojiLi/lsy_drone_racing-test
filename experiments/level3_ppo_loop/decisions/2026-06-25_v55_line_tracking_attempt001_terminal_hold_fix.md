# v55 Tracker Decision: Fix Line Tracking Terminal Hold Semantics

Date: 2026-06-25

Decision: `launch_tracker_structural_fix`

Failed stage:

```text
line_tracking
```

## Decision

`line_tracking` attempt001 failed the stage gate, but the next move is not more
identical training. First fix the terminal reference semantics for finite
polyline tasks.

Approved fix:

```text
For polyline tracker tasks, once distance_along reaches the end of the path,
emit a terminal hold reference at the final point with desired_speed = 0.
```

This keeps the task coherent:

```text
active path phase: follow the moving point and desired velocity
terminal phase: stay at the final point and slow to zero
```

## Evidence

The final checkpoint was safe and close to the line but failed:

```text
success_rate = 1.0
crash_rate = 0.0
mean_cross_track_error_m = 0.07248250395059586
p90_cross_track_error_m = 0.22865745425224304
mean_speed_error_mps = 0.3112734258174896
mean_action_delta_l2 = 0.010021119378507137
```

The 0.9m line at 0.38m/s ends after roughly 2.4s, but evaluation continues for
500 steps at 50 Hz. With the old semantics, the current reference point is
clamped to the path endpoint while desired speed remains nonzero.

## Required Validation

Use builder/checker gate because this changes reference/evaluator semantics.

Checker must verify:

```text
jq empty experiments/level3_ppo_loop/state.json experiments/level3_ppo_loop/tracker_qualification_gates.json
git diff --exit-code -- config/level3.toml
pixi run -e tests ruff check lsy_drone_racing/control/level3_reference_tracker.py tests/unit/control/test_level3_reference_tracker_env.py scripts/evaluate_level3_tracker_stage.py scripts/check_level3_tracker_stage_gate.py
pixi run -e tests python -m pytest tests/unit/control/test_level3_reference_tracker_env.py tests/unit/scripts/test_level3_tracker_stage_evaluator.py tests/unit/scripts/test_level3_tracker_stage_gate.py -q
```

After checker passes, re-evaluate:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/line_tracking/v55_tracker_line_tracking_from_brake_attempt001_final.ckpt
```

If the fixed-semantics gate passes, unlock `heading_tracking`. If it still
fails, launch `line_tracking` attempt002 with a speed-tracking reward/curriculum
change rather than promoting.
