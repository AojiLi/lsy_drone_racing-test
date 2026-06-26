# v55 Decision: Demote Gate-Aperture Stage And Promote Planner Smoke

## Decision

Stop required `gate_aperture_reference` training. It is now an optional
diagnostic, not a mandatory stage in the tracker qualification ladder.

The next required stage is `planner_integration_smoke` on unchanged
`config/level3.toml`, using the zigzag-qualified tracker checkpoint:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/zigzag_or_lemniscate_tracking/v55_tracker_zigzag_from_curve_attempt001_step_042959360.ckpt
```

## Reason

The architecture is:

```text
upper planner -> local reference trajectory -> PPO tracker -> roll/pitch/yaw/thrust
```

Under this architecture, the bottom PPO should not be trained to own gate
crossing semantics through reward-shaped gate-aperture tasks. The upper planner
owns pre-gate alignment, aperture point choice, post-gate recovery point choice,
and slowdown/replan behavior. The bottom PPO owns stable reference tracking.

The first 10 free-space tracker stages through
`zigzag_or_lemniscate_tracking` already passed. `gate_aperture_reference`
attempt001 learned no-crash centering but parked before the plane, and attempt002
was stopped after two intermediate checkpoints. Continuing that reward-shaped
lane risks optimizing a task that is no longer the right abstraction boundary.

## Superseded Work

This decision supersedes:

```text
experiments/level3_ppo_loop/decisions/2026-06-26_v55_gate_aperture_attempt002_phase_completion_shaping.md
```

The checker-approved code/config for gate-aperture diagnostics can remain in the
repo because the new reward coefficients default to zero and the stage is now
optional. Do not launch the approved attempt002 long training unless a later
decision explicitly reopens gate-aperture diagnostics.

## Required Loop Changes

- `zigzag_or_lemniscate_tracking.next_stage` is now
  `planner_integration_smoke`.
- `planner_integration_smoke.prerequisite_stage` is now
  `zigzag_or_lemniscate_tracking`.
- `gate_aperture_reference` is marked `optional_diagnostic` and `blocking:
  false`.
- `state.json` current tracker stage is now `planner_integration_smoke`.

## Next Action

Run planner integration smoke with the zigzag-qualified tracker and the upper
planner on unchanged `config/level3.toml`. If it fails, diagnose whether the
failure is:

- planner-reference design: wrong waypoint timing, speed, heading, slowdown, or
  aperture/post-gate point choice;
- tracker reference-following gap: the zigzag-qualified tracker cannot follow a
  planner-generated trajectory family;
- integration bug: action/observation/reference packaging mismatch.

Do not approve planner-driven long Level3 training until
`planner_integration_smoke` passes.
