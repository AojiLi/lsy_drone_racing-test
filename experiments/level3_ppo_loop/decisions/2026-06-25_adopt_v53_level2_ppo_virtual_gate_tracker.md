# Decision: Adopt Level2 PPO Virtual-Gate Tracker For V53

Date: 2026-06-25

Decision: `launch_named_structural_lane`

Lane:

```text
v53_completion_first_hybrid_planner_controller
```

## Decision

Adopt the user's proposed v53 implementation path:

```text
upper planner generates reference point / reference velocity / desired heading
-> virtual Level2 local-gate observation adapter
-> Level2 PPO tracker checkpoint
-> roll/pitch/yaw/thrust
```

## Tracker Checkpoint

Use the stable Level2 PPO checkpoint first:

```text
lsy_drone_racing/control/checkpoints/level2_DR_latencyobs_middlemanuever/level2_DR_latencyobs_middlemanuever_final.ckpt
```

Observed properties:

- observation layout: `obstacle_heading_xy_v1`;
- hidden dim: `256`;
- actor input dim: `103`;
- action dim: `4`;
- action semantics: `[roll, pitch, yaw, thrust]`.

## Rationale

The Level2 checkpoint already has useful low-level flight/body-control behavior,
but it is not a complete Level3 controller. The planner should make route and
timing decisions; the Level2 PPO should only track a local synthetic target.

This avoids asking PPO to both choose the route and fly the body. It also uses
the Level3 `sensor_range = 0.7` fact directly: slow down near visibility range,
observe true geometry, generate a short local reference, then track it.

## Implementation Requirements

- Implement the adapter inside
  `lsy_drone_racing/control/level3_hybrid_planner_controller.py`.
- Convert planner reference into a synthetic Level2-style local gate/observation.
- Do not mutate the original Level2 checkpoint.
- Log tracker diagnostics: virtual gate center/yaw, reference error, desired
  velocity, phase, target gate, and selected aperture.
- Keep hard eval on unchanged `config/level3.toml`.
- Do not use static seed replay.
- Do not record hybrid-controller success as PPO success.

## Next Action

Run the builder/checker implementation gate, then smoke eval on seeds `101-105`.
Only run dev seeds `1-20` if smoke is finite and behavior is sensible.
