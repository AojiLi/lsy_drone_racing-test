# Decision: Launch Completion-First Trajectory Planner + PPO Tracker

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

The user then clarified the preferred structure: an upper planner, for example
MPPI or a geometric planner, should generate a short trajectory, and PPO or a
low-level tracker should follow that trajectory.

## Decision

Stop treating the next move as a pure PPO or planner-as-observation experiment.
Also stop continuing v52 as another local MPPI coefficient sweep.

Launch a hybrid/controller lane with this preferred action path:

```text
upper planner / MPPI / geometric route module
-> local reference trajectory
-> PPO or low-level trajectory tracker
-> [roll, pitch, yaw, thrust]
```

Direct non-PPO action output remains allowed for tracker baselines, but the main
experiment should test trajectory factorization rather than another pure MPPI
action-cost sweep.

## Required Controller Behavior

The controller should prioritize:

- stable takeoff and height acquisition;
- conservative cruise to a pre-gate point;
- slowdown near the `0.7m` gate/obstacle visibility range;
- local trajectory replanning after true geometry becomes visible;
- gate-frame alignment before crossing;
- obstacle-aware aperture selection;
- reference trajectory tracking;
- controlled crossing and post-gate recovery;
- completion rate before speed.

## Boundaries

Approved:

- direct planner/state-machine/controller action output;
- upper planner trajectory generation plus PPO/low-level tracker;
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
first v53 candidate. It should generate a local reference trajectory, expose
tracker diagnostics, and use PPO or a minimal low-level tracker to follow that
reference. Run builder/checker verification, then evaluate smoke seeds
`101-105` and dev seeds `1-20` on unchanged `config/level3.toml`.
