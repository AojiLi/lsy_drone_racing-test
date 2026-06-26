# V56 Task 4 Recover Semantic Guard Analysis

## Summary

Task 4 fixed the v56 semantic guard: the planner no longer enters recover while
the environment `target_gate` remains unchanged. The run is still not a v56
performance pass. Gate0 pass remains `2/20`, first-gate progress remains
`19/20`, and contact rose to `20/20`.

## Fixed Evaluation

- Stage: `planner_integration_smoke`
- Seeds: `101-120`
- Steps: `500`
- Checkpoint:
  `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- Metrics:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task4_recover_semantic_guard_500step_metrics.json`
- Trace:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task4_recover_semantic_guard_500step_trace.json`
- Compatibility checker:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_task4_recover_semantic_guard_500step_gate.json`

## Builder And Checker Gate

Changed files:

- `lsy_drone_racing/control/level3_reference_tracker.py`
- `tests/unit/control/test_level3_reference_tracker_env.py`

The implementation removed automatic phase-5 recover entry from local X alone:

- `_initial_phase_id` no longer returns phase `5`;
- `_advance_phase` now clips geometric planner phases to `1..4`;
- tests assert that same-target after-plane state remains `cross`, not
  `recover`.

Checks:

- `pixi run -e tests pytest tests/unit/control/test_level3_reference_tracker_env.py tests/unit/scripts/test_level3_tracker_stage_evaluator.py`
  passed: `21 passed, 1 warning`.
- Read-only checker reported `ALL GREEN`: only the planner and tests changed,
  `config/level3.toml` was untouched, ruff passed, and diff check was clean.

## V56 Target Result

Task 4 result:

- first-gate progress: `19/20`
- gate0 pass: `2/20` seeds `113, 120`
- contact: `20/20`
- early termination: `2/20`
- all finite: `true`
- `config/level3.toml`: unchanged
- recover-before-env-switch rows: `0`
- fake recover count: `0`

Comparison:

| Metric | Baseline v55 | Task1 | Task4 |
| --- | ---: | ---: | ---: |
| gate0 pass | `3/20` | `2/20` | `2/20` |
| first-gate progress | `20/20` | `19/20` | `19/20` |
| contact | `15/20` | `19/20` | `20/20` |
| early termination | `2/20` | `2/20` | `2/20` |
| recover before env switch | nonzero | nonzero | `0` |

The legacy checker passed, but it remains compatibility evidence only.

## Trace Findings

Phase row counts:

- phase 1: `373`
- phase 2: `493`
- phase 3: `1387`
- phase 4: `197`
- phase 5: `0`

Cross entries occurred in `10/20` seeds:

`101, 102, 106, 109, 111, 113, 115, 117, 119, 120`

Raw gate-local Y/Z norm at first cross entry:

- min: `0.138`
- median: `0.243`
- p75: `0.290`
- max: `2.707`

`abs(gate_local_vx)` at first cross entry:

- min: `0.033`
- median: `0.251`
- p75: `0.364`
- max: `0.410`

Large same-gate Y/Z errors remain near the gate plane. Seed `106` is the clearest
case: it starts past the plane, no longer enters recover, but still stays in
cross and contacts without a real gate switch.

Failure buckets:

- passed gate0 then contact later: `113, 120`
- immediate or early contact: `114, 118`
- contact before gate plane: `105, 107`
- contact near gate without pass: `103, 104, 108, 110, 112, 116`
- cross-phase contact without pass: `101, 102, 106, 109, 111, 115, 117, 119`

## Main-Agent Diagnosis

Task 4 achieved the semantic repair it was supposed to achieve. It did not
improve the v56 performance target. The next actionable failure is near-plane
same-gate contact with large Y/Z error. Continuing to cross in that state is
unsafe; reducing cross speed alone may not help if the vehicle is already
outside the aperture corridor.

Next iteration should implement Task 3 near-plane backout as one planner
strategy knob.
