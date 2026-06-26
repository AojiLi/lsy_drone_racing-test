# Decision: V56 Task 2 Failed, Add Aperture Trace Support

## Decision

Hold planner strategy tuning. Do not launch another planner knob yet.

Next action:

```text
v56_aperture_trace_metric_support
```

This is diagnostic support only. It may add per-step trace fields and tests, but
it must not change planner behavior.

## Evidence

Task2 changed phase-4 desired speed from `0.52` to `0.32`, and the trace proves
the change was wired:

- every phase-4 row had `desired_speed = 0.32`;
- semantic guard stayed clean:
  - phase5 rows: `0`
  - fake recover: `0`
  - recover-before-switch: `0`

However, fixed-smoke performance did not improve:

- gate0 pass: `2/20`
- first-gate progress: `19/20`
- contact: `20/20`
- early termination: `2/20`
- all finite: `true`
- `config/level3.toml` unchanged

Task1, Task3, and Task2 all failed to improve gate0 pass. Task4 fixed semantics
only. Continuing to tune planner constants without exact aperture-relative
trace would be under-instrumented.

## Required Metric Support

Add per-step fields to the Level3 planner smoke trace:

```text
aperture_y
aperture_z
aperture_yz_error
```

Definition:

```text
aperture_yz_error = hypot(gate_local_y - aperture_y, gate_local_z - aperture_z)
```

The values should come from controller diagnostics already emitted by the
reference tracker controller when possible.

## Acceptance For Metric-Support Rerun

Allowed:

- trace/evaluator diagnostics;
- tests for trace fields and recomputation.

Forbidden:

- PPO training;
- reward changes;
- observation-layout changes;
- tracker checkpoint changes;
- MPPI or planner action output;
- planner strategy changes;
- editing `config/level3.toml`.

The fixed smoke should remain behaviorally equivalent to Task2 unless the new
instrumentation reveals a measurement bug:

- gate0 pass: expected `2/20`, seeds `113, 120`
- first-gate progress: expected `19/20`
- contact: expected `20/20`
- early termination: expected `2/20`
- all finite: `true`
- `level3_toml_diff_clean = true`
- recover-before-gate-switch: `0`
- phase5 rows: `0`

The analysis must report:

- aperture-relative cross-entry Y/Z error p50/p75/max;
- near-plane aperture Y/Z error for pass versus fail seeds;
- large-Y/Z cross-attempt count;
- phase contact counts;
- all 20 seed failure buckets.
