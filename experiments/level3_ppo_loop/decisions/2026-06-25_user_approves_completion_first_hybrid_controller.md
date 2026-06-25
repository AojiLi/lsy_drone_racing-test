# Decision: Launch Completion-First Hybrid Planner Controller

Date: 2026-06-25

Decision: `launch_named_structural_lane`

New lane:

```text
v53_completion_first_hybrid_planner_controller
```

## User Approval

The user approved relaxing the pure-PPO-controller constraint for the next
Level3 attempt. The immediate goal is reliable completion on unchanged
`config/level3.toml`; successful runs around `15s-20s` are acceptable as an
intermediate milestone.

## Decision

Stop treating the next move as a pure PPO or planner-as-observation experiment.
Also stop continuing v52 as another local MPPI coefficient sweep.

Launch a non-PPO hybrid/controller lane that may directly output
`[roll, pitch, yaw, thrust]` actions using explicit phase logic and planning.

## Required Controller Behavior

The controller should prioritize:

- stable takeoff and height acquisition;
- conservative cruise to a pre-gate point;
- slowdown near gate visibility range;
- gate-frame alignment before crossing;
- obstacle-aware aperture selection;
- controlled crossing and post-gate recovery;
- completion rate before speed.

## Boundaries

Approved:

- direct planner/state-machine/controller action output;
- slow-safe completion-first timing;
- MPPI or geometric planning if useful;
- hard eval through `scripts/evaluate_level3_controller.py`.

Not approved:

- changing `config/level3.toml`;
- recording non-PPO success as PPO success;
- static seed replay;
- PPO BC/DAgger/teacher-data generation before a later analysis packet and
  decision explicitly allow it.

## Next Action

Implement `lsy_drone_racing/control/level3_hybrid_planner_controller.py` as the
first v53 candidate, run builder/checker verification, then evaluate smoke
seeds `101-105` and dev seeds `1-20` on unchanged `config/level3.toml`.
