# V56 Aperture Trace Support Analysis

## Summary

This iteration implemented diagnostic support only. It added per-step aperture
trace fields to the Level3 planner smoke trace:

```text
aperture_y
aperture_z
aperture_yz_error = hypot(gate_local_y - aperture_y, gate_local_z - aperture_z)
```

No planner strategy, PPO training, reward, observation layout, checkpoint, MPPI,
or `config/level3.toml` change was made.

The metric support is valid and the fixed smoke remained behaviorally equivalent
to Task2, but v56 still failed its target. The new data argues against more
ordinary one-knob align/cross/backout tuning and points to a reference-geometry
/ tracker-interface problem.

## Fixed Evaluation

- Stage: `planner_integration_smoke`
- Seeds: `101-120`
- Steps: `500`
- Checkpoint:
  `lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt`
- Metrics:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_aperture_trace_support_500step_metrics.json`
- Trace:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_aperture_trace_support_500step_trace.json`
- Compatibility checker:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v56_aperture_trace_support_500step_gate.json`

## Builder And Checker Gate

Changed files:

- `scripts/check_level3_reference_tracker_smoke.py`
- `tests/unit/scripts/test_level3_tracker_stage_evaluator.py`
- `tests/unit/scripts/test_level3_reference_tracker_smoke.py`

Checks:

- `git diff --check`: passed.
- `git diff -- config/level3.toml`: no output.
- `pixi run -e tests ruff check ...`: passed.
- `pixi run -e tests pytest tests/unit/scripts/test_level3_reference_tracker_smoke.py tests/unit/scripts/test_level3_tracker_stage_evaluator.py tests/unit/control/test_level3_reference_tracker_env.py -q`:
  `23 passed, 1 warning`.
- Read-only checker: `ALL GREEN`.

The warning is the existing JAX overflow warning in a vector-env unit test; it
did not fail the gate.

## V56 Target Result

- first-gate progress: `19/20`
- gate0 pass: `2/20`, seeds `113, 120`
- contact: `20/20`
- early termination: `2/20`, seeds `114, 118`
- all finite: `true`
- `config/level3.toml`: unchanged
- phase5 rows: `0`
- recover-before-switch rows: `0`

The legacy checker passed because it only requires the older smoke contract
(`gate0_pass_count >= 1`). It is compatibility evidence only. V56 acceptance
requires `gate0 pass >= 10/20`, `contact <= 8/20`, and first-gate progress
`20/20`, so v56 is not complete.

## Aperture Metric Validation

Trace rows: `2456`.

The aperture fields are present and finite on every trace row:

- missing aperture fields: `0`
- non-finite aperture values: `0`
- formula recomputation max error: `2.22e-16`

This is sufficient to use `aperture_yz_error` for future planner analysis.

Important caveat: terminal contact trace rows are post-step terminal
observations and can contain reset/placeholder-like state jumps. Alignment and
crossing analysis should use non-terminal rows or the penultimate row per seed,
not the final terminal contact row.

## Trace Findings

Cross-entry rows, excluding terminal contact rows:

- cross-entry seeds: `101, 102, 109, 111, 113, 115, 117, 119, 120`
- cross-entry aperture error:
  - median `0.172m`
  - p75 `0.181m`
  - max `0.218m`
- cross-entry absolute gate-local X speed:
  - median `0.265m/s`
  - p75 `0.375m/s`
  - max `0.410m/s`
- wrong cross entries using `aperture_yz_error > 0.25m` or `abs(vx) > 0.85m/s`:
  `0`

Near-plane phase-4 rows, excluding terminal contact rows:

- aperture error:
  - median `0.153m`
  - p75 `0.180m`
  - max `0.218m`
- absolute gate-local X speed:
  - median `0.522m/s`
  - p75 `0.695m/s`
  - max `0.809m/s`

Large-Y/Z cross attempts near the plane:

- active rows with phase 4, `abs(gate_local_x) < 0.35`, and
  `aperture_yz_error > 0.30`: `0`
- seeds: none

Phase at penultimate row before contact:

- phase1: `1`
- phase2: `1`
- phase3: `9`
- phase4: `7`

## Failure Buckets

- `passed_gate0_then_contact_later`: `2` seeds `[113, 120]`
- `contact_before_gate_plane`: `10` seeds
  `[101, 102, 105, 107, 108, 111, 112, 115, 116, 119]`
- `contact_near_gate_without_pass`: `6` seeds
  `[103, 104, 106, 109, 110, 117]`
- `crossed_plane_far_outside_aperture_timeout`: `0` seeds
- `immediate_or_early_contact`: `2` seeds `[114, 118]`
- `other_contact_no_pass`: `0`

The trace-metrics reviewer also classified overlapping contact modes and found
that contact is concentrated in phase3/phase4 near the gate.

## Three Review Results

Planner trace metrics reviewer:

- v56 target failed.
- aperture fields are complete and numerically correct.
- cross-entry Y/Z is usually acceptable.
- phase4 actual gate-local X speed remains too high despite desired speed
  `0.32m/s`.
- main failure is contact conversion around phase3/phase4.

Planner semantics checker:

- `ALL GREEN`.
- no `config/level3.toml`, PPO, reward, observation, checkpoint, MPPI, or
  training change.
- phase5 rows: `0`.
- same-target recover proxy: `0`.
- real gate pass remains tied to environment `target_gate` transition.
- future alignment analysis should ignore terminal contact rows.

Planner next-hypothesis reviewer:

- recommend `launch_named_structural_planner_lane`.
- proposed lane: `v57_reference_geometry_tracker_interface_audit`.
- ordinary one-knob tuning is no longer well supported by the aperture evidence.

## Main-Agent Diagnosis

The aperture trace support succeeded. The result is more informative than
encouraging:

- Task1 align gating, Task3 backout, and Task2 cross slowdown all failed to
  improve beyond `2/20`.
- Task4 fixed illegal same-target recover but did not improve performance.
- New aperture metrics show that cross entry is usually not grossly misaligned.
- Phase4 desired speed reduction does not reliably reduce actual gate-local X
  speed.

The likely bottleneck is not another small threshold. It is the interface between
the geometric planner reference and the PPO tracker: reference jumps, phase
switch timing, lookahead geometry, or speed/heading packaging may be producing
commands that the tracker cannot physically follow safely near the gate.

## Decision Direction

Hold for user review:

```text
hold_for_user_review
```

This satisfies the v56 goal stop condition: several one-knob iterations failed
to improve gate0 pass/contact meaningfully, and the new aperture trace shows
that continuing ordinary threshold tuning is low confidence.

If the user chooses to continue after review, the recommended next candidate is
a new planner-only structural audit:

```text
v57_reference_geometry_tracker_interface_audit
```

That future lane should remain planner-only and must not train PPO or modify
`config/level3.toml`. Its purpose would be to audit and redesign the reference
geometry / tracker interface before another 500-step smoke.
