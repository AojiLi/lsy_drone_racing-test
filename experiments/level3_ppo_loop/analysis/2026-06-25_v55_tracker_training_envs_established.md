# v55 Tracker Training Environments Established

Date: 2026-06-25

## Decision Context

The v54 reference-tracker smoke proved the action path was finite, but it did
not prove useful Level3 behavior: checkpoint-backed smoke still had no gate-0
passes. The next tracker-loop step is therefore not long Level3 training. It is
to train the bottom PPO as a reliable reference follower before planner
integration.

## Implemented

- Added `config/level3_tracker_free_space.toml`.
  - Uses Level3-like first-principles dynamics, `cf21B_500`, 50 Hz env
    frequency, and attitude action mode.
  - Provides dummy far-away gate/obstacle objects only to satisfy the
    `DroneRacing-v0` observation structure.
  - `ReferenceTrackerEnv` ignores gate/obstacle context in this mode.
- Added `config/level3_tracker_gate_aperture.toml`.
  - Uses a controlled single-gate mini task after free-space tracking is stable.
  - Keeps Level3-like dynamics and action interface.
- Extended `ReferenceTrajectoryGenerator` with v55 tracker tasks:
  - `hover`
  - `point_hold`
  - `point_reach`
  - `brake_to_point`
  - `line_tracking`
  - `heading_tracking`
  - `multi_point_reference`
  - `l_shape_tracking`
  - `curve_tracking`
  - `zigzag_or_lemniscate_tracking`
  - `gate_aperture_reference`
  - `level3`
- Added tracker environment mode resolution:
  - `free_space`
  - `gate_aperture`
  - `level3`
  - `auto`
- Updated the tracker PPO training CLI with `--tracker-env-mode` and the
  expanded task set.
- Added unit tests for task aliases, config/mode resolution, dummy-object
  isolation, and invalid task/mode combinations.

## Hard Boundary Check

`config/level3.toml` was not modified. These configs are training and
qualification environments only. Final Level3 acceptance remains unchanged
`config/level3.toml`.

## Validation

Passed:

```bash
pixi run -e tests ruff check \
  lsy_drone_racing/control/level3_reference_tracker.py \
  lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  tests/unit/control/test_level3_reference_tracker_env.py
```

```bash
pixi run -e tests python -m pytest \
  tests/unit/control/test_level3_reference_tracker_env.py -q
```

Result: `4 passed`.

Config load check:

```text
level3_tracker_free_space.toml DroneRacing-v0 attitude 1 1 free_space
level3_tracker_gate_aperture.toml DroneRacing-v0 attitude 1 1 gate_aperture
level3.toml DroneRacing-v0 attitude 4 4 none
```

Reset/step smoke passed for:

- `level3_tracker_free_space.toml` with `line_tracking`
- `level3_tracker_gate_aperture.toml` with `gate_aperture_reference`

Extreme short training smoke passed and saved checkpoints under `/tmp` for:

- free-space `line_tracking`
- gate-aperture `gate_aperture_reference`

## Next Required Work

Run bounded tracker qualification before any long planner-driven Level3
training. The first qualification goal should measure hover/point/line/braking
tracking errors, overshoot, crash rate, action smoothness, and finite actions.

Only after free-space tracking is stable should the loop move to
`gate_aperture_reference`, then unchanged `config/level3.toml` planner smoke.
