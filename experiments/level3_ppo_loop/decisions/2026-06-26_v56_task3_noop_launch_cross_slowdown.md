# Decision: V56 Task 3 No-Op, Launch Task 2 Cross Slowdown

## Decision

Do not continue widening Task 3 backout yet. Launch exactly one next planner
knob:

```text
v56_task2_cross_slowdown
```

Change only the phase-4 cross desired speed, for example:

```text
0.52 m/s -> 0.32 m/s
```

## Evidence

Task 3 did not change the rollout:

- Task3 trace is byte-identical to Task4 trace;
- phase `4 -> 3` backout transitions: `0`;
- gate0 pass: `2/20`;
- first-gate progress: `19/20`;
- contact: `20/20`;
- recover-before-switch: `0`;
- phase5 rows: `0`.

Task 3 was implemented within scope, but it did not address the active failure
path. The remaining cross-phase contacts are more consistent with cross speed
and reference aggressiveness than with large Y/Z backout.

The next-hypothesis reviewer recommended Task 2 because phase-4 terminal-contact
seeds often have acceptable aperture-relative Y/Z but high gate-local speed,
while phase-4 desired speed remains `0.52 m/s`.

## Guardrails

Allowed:

- change only phase-4 cross speed in `GeometricSlowGatePlanner._phase_points`;
- add/update tests that verify the cross-speed constant if useful.

Forbidden:

- changing align thresholds;
- changing Task3 backout thresholds;
- changing recover semantics;
- PPO training;
- reward changes;
- observation-layout changes;
- tracker checkpoint changes;
- MPPI or planner action output;
- editing `config/level3.toml`.

## Acceptance For Task 2

Fixed smoke:

- unchanged `config/level3.toml`;
- fixed v55 zigzag tracker checkpoint;
- seeds `101-120`;
- `500` steps;
- only environment `target_gate` transition counts as gate pass.

Local Task 2 gate:

- `all_finite = true`
- `recover_before_gate_switch_count = 0`
- `fake_recover_count = 0`
- `phase5_rows = 0`
- `gate0_pass_count >= 5/20`
- `contact_count <= 12/20`
- `cross_phase_contact_without_pass_count <= 4/20`
- `first_gate_progress_count >= 19/20`, preferably `20/20`
- `early_termination_count <= 6/20`

Full v56 target remains:

- first-gate progress `20/20`
- gate0 pass `>=10/20`
- contact `<=8/20`
- early termination `<=6/20`
- all finite
- unchanged `config/level3.toml`
