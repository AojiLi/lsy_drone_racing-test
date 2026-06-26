# Decision: V56 Aperture Trace Support Complete, Launch V57 Interface Audit

## Decision

Launch a named structural planner lane:

```text
v57_reference_geometry_tracker_interface_audit
```

Do not continue ordinary v56 one-knob planner tuning yet.

Decision type:

```text
launch_named_structural_lane
```

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

## Interpretation

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

Task1, Task3, and Task2 have all failed to improve gate0 pass. Task4 fixed
recover semantics only. Continuing to tune threshold constants such as cross
speed, Y/Z gate, or backout threshold is now low confidence.

## V57 Scope

`v57_reference_geometry_tracker_interface_audit` should inspect and redesign the
interface between the geometric planner and the PPO tracker.

Allowed:

- trace/evaluator diagnostics;
- planner reference geometry changes;
- smoother lookahead/reference generation;
- phase-transition timing changes;
- reference speed/heading packaging changes;
- tests for reference continuity and no illegal recover behavior;
- fixed smoke on seeds `101-120`, `500` steps.

Forbidden:

- PPO training;
- reward changes;
- observation-layout changes;
- tracker checkpoint changes;
- MPPI or planner action output;
- editing `config/level3.toml`;
- custom pass checker driving recover or next-gate logic.

## V57 Questions

The next lane should answer:

- Are reference points jumping too far near phase transitions?
- Does phase3 -> phase4 happen before the tracker has actually braked?
- Is `desired_speed` encoded in a way the tracker can follow, or is geometry
  dominating the command?
- Is the pre -> aperture -> post segment too short or too sharp for the tracker?
- Does the tracker need a smoother rolling lookahead instead of discrete phase
  references around the gate plane?

## Acceptance For V57 First Packet

Before another behavioral planner smoke, write a V57 audit packet that reports:

- reference position jump distribution around phase transitions;
- reference-to-drone error near phase3/phase4;
- desired speed versus actual gate-local X speed;
- phase transition timing relative to `gate_local_x`, `aperture_yz_error`, and
  `gate_local_vx`;
- whether terminal contact rows are excluded from alignment metrics;
- a single named first V57 change, or a hold if the audit finds missing
  instrumentation.

Any V57 code change must use the builder/checker gate and preserve the immutable
Level3 target config.
