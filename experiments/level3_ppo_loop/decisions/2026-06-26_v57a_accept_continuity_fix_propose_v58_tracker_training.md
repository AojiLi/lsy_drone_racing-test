# Decision: V57A Accepts Continuity Fix And Proposes V58 Tracker Training

## Decision

Accept the v57a planner-interface fix as implemented.

Do not keep tuning ordinary geometric planner thresholds as the immediate next
move.

Propose the next structural lane:

```text
v58_tracker_planner_like_reference_training
```

Decision type:

```text
launch_named_structural_lane_proposal
```

## Evidence

V57A used unchanged `config/level3.toml`, seeds `101-120`, 500 steps, and the
fixed v55 zigzag-qualified tracker checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
```

No PPO training, reward change, observation-layout change, checkpoint change,
algorithm change, MPPI, or `config/level3.toml` edit was performed.

Builder/checker gate passed:

```text
ALL GREEN
```

Required checks:

- tests: `23 passed, 1 warning`;
- ruff: `All checks passed!`;
- `git diff -- config/level3.toml`: clean.

## Result

V57A successfully reduced the cross-entry discontinuity:

- phase3 -> phase4 reference jump median: `0.740m` -> `0.280m`;
- phase3 -> phase4 reference error median: `0.783m` -> `0.340m`;
- phase3 -> phase4 action delta median: `0.727` -> `0.491`.

But Level3 smoke outcomes did not improve:

- gate0 pass: still `2/20`, seeds `113, 120`;
- first-gate progress: still `19/20`;
- contact: still `20/20`;
- early termination: still `2/20`;
- all finite: `true`;
- phase5 rows: `0`.

Near-plane phase4 speed also stayed too high:

- median actual abs gate-local X speed: `0.522m/s` -> `0.521m/s`;
- p75 actual abs gate-local X speed: `0.695m/s` -> `0.694m/s`.

## Diagnosis

The planner no longer gives the tracker a large abrupt cross-entry jump.
Therefore, if the tracker still enters the gate plane too fast and contacts
near the aperture, the next most likely bottleneck is the low-level tracker's
planner-like reference following and braking ability.

This is the exact v58 trigger from the v57 decision packet:

```text
smooth/reasonable references, but tracker still cannot slow, brake, or avoid contact
```

## V58 Scope

V58 should not train a direct Level3 racing policy. It should train a stronger
low-level tracker for references that look like the planner's real commands:

- smooth point following;
- brake-to-point;
- short line / L / curve segments;
- pre-gate -> aperture -> post-gate reference segments;
- low-speed crossing at `0.25-0.35m/s`;
- low overshoot and stable heading;
- ability to reduce actual gate-local X speed from `~0.7m/s` toward the
  commanded range before crossing.

The upper planner remains responsible for route choice and gate geometry.
The bottom PPO tracker remains responsible for following reference points and
velocities.

## Guardrails

- Do not modify `config/level3.toml`.
- Do not call v57a a Level3 success improvement; it is an interface cleanup.
- Do not resume long Level3 training from this smoke.
- Do not mix MPPI action output into this PPO-tracker lane.
- Keep the planner+tracker deployment contract:

```text
Level3 observation / geometry
-> deterministic planner reference
-> PPO tracker
-> roll / pitch / yaw / thrust
```

## Next Action

Prepare and run a v58 tracker-training goal only after writing a clear v58
training packet with:

- planner-like reference curriculum;
- explicit stage metrics for braking, overshoot, speed tracking, and heading;
- fixed validation seeds;
- W&B logging if long training is launched;
- unchanged `config/level3.toml` hard smoke after tracker qualification.
