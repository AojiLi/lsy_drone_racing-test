# V56 Task 2 Cross Slowdown Analysis

## Summary

Task 2 reduced phase-4 cross desired speed from `0.52 m/s` to `0.32 m/s`.
The change was wired correctly and preserved all semantic guards, but it did not
improve the v56 smoke result. Gate0 pass stayed `2/20`, first-gate progress
stayed `19/20`, and all `20/20` seeds still ended in contact.

## Fixed Evaluation

- Stage: `planner_integration_smoke`
- Seeds: `101-120`
- Steps: `500`
- Checkpoint:
  `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- Metrics:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task2_cross_slowdown_500step_metrics.json`
- Trace:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task2_cross_slowdown_500step_trace.json`
- Compatibility checker:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task2_cross_slowdown_500step_gate.json`

## Builder And Checker Gate

Changed files:

- `lsy_drone_racing/control/level3_reference_tracker.py`
- `tests/unit/control/test_level3_reference_tracker_env.py`

The implementation added `CROSS_SPEED_MPS = 0.32` and changed phase 4 to use
that constant. Tests assert the cross reference speed is `0.32`.

Checks:

- `pixi run -e tests pytest tests/unit/control/test_level3_reference_tracker_env.py tests/unit/scripts/test_level3_tracker_stage_evaluator.py`
  passed: `22 passed, 1 warning`.
- Read-only checker reported `ALL GREEN`: only cross speed and a test assertion
  changed, `config/level3.toml` was untouched, Task4 recover guard was
  preserved, ruff passed, and diff check was clean.

## V56 Target Result

Task 2 result:

- first-gate progress: `19/20`
- gate0 pass: `2/20` seeds `113, 120`
- contact: `20/20`
- early termination: `2/20`
- all finite: `true`
- `config/level3.toml`: unchanged
- recover-before-env-switch rows: `0`
- fake recover count: `0`
- phase5 rows: `0`

Comparison:

| Run | Gate0 Pass | First-Gate Progress | Contact | Phase4 Desired Speed |
| --- | ---: | ---: | ---: | ---: |
| Baseline v55 | `3/20` | `20/20` | `15/20` | `0.52` |
| Task4 | `2/20` | `19/20` | `20/20` | `0.52` |
| Task3 | `2/20` | `19/20` | `20/20` | `0.52` |
| Task2 | `2/20` | `19/20` | `20/20` | `0.32` |

The legacy checker passed, but it remains compatibility evidence only.

## Trace Findings

Trace reviewer findings:

- phase-4 desired speed changed as intended: every phase-4 trace row has
  `desired_speed = 0.32`;
- actual gate-local speed barely changed:
  - Task4 median phase-4 `abs(vx)`: about `0.540 m/s`
  - Task2 median phase-4 `abs(vx)`: about `0.539 m/s`
  - Task2 p75 phase-4 `abs(vx)`: about `0.703 m/s`
  - Task2 max phase-4 `abs(vx)`: about `0.815 m/s`
- cross-phase contact without pass stayed `8/20`;
- no new gate0 pass seeds appeared;
- seed `117`, which passed in the baseline, remained a same-gate contact.

Failure buckets:

- passed gate0 then contact later: `113, 120`
- immediate or early contact: `114, 118`
- contact before gate plane: `105, 107`
- contact near gate without pass: `103, 104, 108, 110, 112, 116`
- cross-phase contact without pass: `101, 102, 106, 109, 111, 115, 117, 119`

## Main-Agent Diagnosis

The desired-speed knob is wired, but the bottom tracker does not sufficiently
reduce actual gate-local velocity in phase 4. Task1, Task3, and Task2 have now
all failed to improve gate0 pass. Task4 fixed semantics, but did not improve
performance.

Before another planner-strategy knob, add per-step aperture trace support:

- `aperture_y`
- `aperture_z`
- `aperture_yz_error`

Then rerun the fixed smoke to compute exact aperture-relative cross-entry and
near-plane errors. This is diagnostic support, not a new planner strategy.
