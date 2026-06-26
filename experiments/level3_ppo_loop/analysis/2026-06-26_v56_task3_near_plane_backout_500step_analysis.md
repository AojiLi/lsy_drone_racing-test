# V56 Task 3 Near-Plane Backout Analysis

## Summary

Task 3 added a near-plane Y/Z backout rule, but the fixed 500-step smoke showed
no behavioral change versus Task 4. The trace is byte-identical to Task 4, no
phase `4 -> 3` backout occurred, and v56 performance remains below both the
target and the v55 baseline.

## Fixed Evaluation

- Stage: `planner_integration_smoke`
- Seeds: `101-120`
- Steps: `500`
- Checkpoint:
  `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- Metrics:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task3_near_plane_backout_500step_metrics.json`
- Trace:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task3_near_plane_backout_500step_trace.json`
- Compatibility checker:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task3_near_plane_backout_500step_gate.json`

## Builder And Checker Gate

Changed files:

- `lsy_drone_racing/control/level3_reference_tracker.py`
- `tests/unit/control/test_level3_reference_tracker_env.py`

The implementation added exactly one planner knob:

```text
if phase >= 4 and abs(gate_local_x) < 0.35 and yz_error > 0.30:
    phase = align
```

Checks:

- `pixi run -e tests pytest tests/unit/control/test_level3_reference_tracker_env.py tests/unit/scripts/test_level3_tracker_stage_evaluator.py`
  passed: `22 passed, 1 warning`.
- Read-only checker reported `ALL GREEN` for code scope: `config/level3.toml`
  unchanged, only planner/test files changed, no cross-speed/PPO/reward/checkpoint
  changes, ruff passed, and diff check was clean.

## V56 Target Result

Task 3 result:

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

| Run | Gate0 Pass | First-Gate Progress | Contact | Fake Recover / Phase5 |
| --- | ---: | ---: | ---: | ---: |
| Baseline v55 | `3/20` | `20/20` | `15/20` | nonzero |
| Task1 | `2/20` | `19/20` | `19/20` | nonzero |
| Task4 | `2/20` | `19/20` | `20/20` | `0` |
| Task3 | `2/20` | `19/20` | `20/20` | `0` |

The legacy checker passed, but it remains compatibility evidence only.

## Trace Findings

Trace reviewer findings:

- Task3 trace is byte-identical to Task4 trace.
- Phase row counts are unchanged:
  - phase 1: `373`
  - phase 2: `493`
  - phase 3: `1387`
  - phase 4: `197`
  - phase 5: `0`
- Direct phase `4 -> 3` backout transitions: `0`
- Large-Y/Z cross attempts: `1/20` seed, `12` rows, seed `109`
- Recover guard stayed clean.

Semantic reviewer classified the smoke as failed because:

- Task3 local performance gate was not met;
- gate0 pass remained `2/20`, below the local minimum `>=3/20`;
- contact remained `20/20`, above the local maximum `<=10/20`;
- the backout rule did not visibly trigger in trace.

## Main-Agent Diagnosis

Task 3 was a scoped, valid implementation, but it did not affect the actual
rollout. Continuing to widen the backout condition without better evidence
risks chasing a rule that is not on the main failure path.

The current trace points more strongly at Task 2 cross slowdown:

- phase-4 terminal-contact seeds have aperture-relative errors mostly in the
  `0.11m-0.22m` range;
- gate-local velocity near terminal contact is often high, about `0.65m/s` to
  `0.84m/s`;
- phase-4 desired speed remains `0.52m/s`.

The next iteration should change only phase-4 cross desired speed, e.g.
`0.52 -> 0.32 m/s`, while preserving Task4 semantic guards.
