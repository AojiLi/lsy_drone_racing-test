# Decision: V56 Aperture Trace Support Complete, Hold For User Review

## Decision

Hold v56 for user review.

Decision type:

```text
hold_for_user_review
```

Do not launch another v56 one-knob planner tuning iteration under this goal.
Do not launch v57 automatically from this decision.

## Evidence

The aperture trace support was implemented and independently checked:

- per-step `aperture_y`, `aperture_z`, and `aperture_yz_error` are now emitted;
- formula recomputation max error was `2.22e-16`;
- every one of `2456` trace rows had finite aperture metrics;
- read-only checker reported `ALL GREEN`;
- `config/level3.toml` was unchanged.

The fixed 500-step smoke still failed v56:

- first-gate progress: `19/20`
- gate0 pass: `2/20`, seeds `113, 120`
- contact: `20/20`
- early termination: `2/20`
- all finite: `true`
- phase5 rows: `0`
- recover-before-switch rows: `0`

The legacy planner smoke checker passed, but it is not v56 acceptance. V56 still
requires gate0 pass `>=10/20`, contact `<=8/20`, and first-gate progress
`20/20`.

## Why Hold

The v56 one-knob iterations did not improve first-gate crossing:

- Task1 align stabilization failed the v56 target and exposed illegal
  same-target recover.
- Task4 fixed recover semantics but did not improve performance.
- Task3 near-plane backout produced no behavioral change.
- Task2 cross slowdown was wired, but actual phase4 gate-local speed stayed
  high and gate0 pass stayed `2/20`.
- Aperture trace support showed cross-entry alignment is usually acceptable,
  not grossly wrong.

The new aperture metrics do not support the simple story that the planner is
entering cross while badly off-center:

- cross-entry aperture error median: `0.172m`
- cross-entry aperture error p75: `0.181m`
- cross-entry aperture error max: `0.218m`
- large-Y/Z cross attempts near the plane: `0`

However, near-plane phase4 actual gate-local X speed remains high:

- median `0.522m/s`
- p75 `0.695m/s`
- max `0.809m/s`

This means lowering the planner's phase4 `desired_speed` to `0.32m/s` did not
make the closed-loop system slow enough at the gate.

Continuing to tune threshold constants such as cross speed, Y/Z gate, or
backout threshold is now low confidence. The likely bottleneck is the interface
between planner references and the PPO tracker.

## Recommended Next Direction If Resumed

If the user approves continuing beyond this v56 hold, the recommended next
candidate is:

```text
v57_reference_geometry_tracker_interface_audit
```

That future lane should inspect and redesign the interface between the
geometric planner and the PPO tracker.

Allowed in that future lane:

- trace/evaluator diagnostics;
- planner reference geometry changes;
- smoother lookahead/reference generation;
- phase-transition timing changes;
- reference speed/heading packaging changes;
- tests for reference continuity and no illegal recover behavior;
- fixed smoke on seeds `101-120`, `500` steps.

Still forbidden:

- PPO training;
- reward changes;
- observation-layout changes;
- tracker checkpoint changes;
- MPPI or planner action output;
- editing `config/level3.toml`;
- custom pass checker driving recover or next-gate logic.

## Review Questions For User

- Should the next goal approve `v57_reference_geometry_tracker_interface_audit`?
- Should v57 prioritize reference continuity, phase-transition timing, or
  speed/heading packaging first?
- Should we keep the current v56 planner changes as the starting point, or
  revert ineffective Task2/Task3 knobs before v57?
