# v55 Decision: Use GeometricSlowGatePlanner For Planner Smoke

## Decision

Implement `GeometricSlowGatePlanner` as the first planner-integration smoke
planner for the v55 native PPO reference tracker.

This is not MPPI/MPC and it does not output actions. The deployed action path
remains:

```text
Level3 observation
-> GeometricSlowGatePlanner reference points/speed/heading
-> PPO tracker observation
-> PPO tracker action
-> roll/pitch/yaw/thrust
```

## Rationale

The immediate goal is not fastest Level3 completion. It is to test whether the
already qualified tracker can follow conservative, human-readable references in
unchanged `config/level3.toml`.

The planner uses five phases:

```text
cruise -> slowdown -> align -> cross -> recover
```

It is deliberately conservative:

- low far-field cruise speed;
- slowdown around the first meter before the gate;
- pre-gate alignment before crossing;
- short pre/aperture/post/recovery reference horizon;
- phase hysteresis so it does not bounce near thresholds;
- visible-obstacle waypoint offset as a first safety rule.

## Implementation Scope

Changed:

```text
lsy_drone_racing/control/level3_reference_tracker.py
tests/unit/control/test_level3_reference_tracker_env.py
```

Not changed:

```text
config/level3.toml
PPO tracker network architecture
PPO action output semantics
gate_aperture_reference optional diagnostic status
```

## Validation

Commands run:

```bash
pixi run -e tests pytest tests/unit/control/test_level3_reference_tracker_env.py tests/unit/scripts/test_level3_tracker_stage_evaluator.py tests/unit/scripts/test_level3_tracker_stage_gate.py -q
pixi run -e tests ruff check lsy_drone_racing/control/level3_reference_tracker.py tests/unit/control/test_level3_reference_tracker_env.py
pixi run -e tests python scripts/check_level3_reference_tracker_smoke.py --allow-untrained --task-steps 4 --level3-steps 6 --level3-seeds 101 --output /tmp/v55_geometric_slow_gate_planner_smoke.json
pixi run -e tests python scripts/check_level3_reference_tracker_smoke.py --checkpoint lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt --task-steps 4 --level3-steps 8 --level3-seeds 101 --output /tmp/v55_geometric_slow_gate_planner_checkpoint_smoke.json
```

Results:

```text
unit tests: 21 passed, 1 known JAX warning
ruff: passed
untrained micro smoke: all_finite=true
checkpoint micro smoke: all_finite=true, checkpoint_backed=true
config/level3.toml: unchanged
```

The micro smokes are plumbing/semantic checks only. They are not success-rate
evidence.

## Next Action

Run the required `planner_integration_smoke` with the zigzag-qualified tracker:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
```

Use unchanged `config/level3.toml` and evaluate seeds `101-120`. If it fails,
inspect generated references, phase transitions, speed/heading aggressiveness,
obstacle offset behavior, and tracker tracking error before considering MPPI or
additional tracker training.
