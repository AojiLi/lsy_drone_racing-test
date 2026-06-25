# Decision: Refine V53 To Planner Trajectory Plus PPO Tracker

Date: 2026-06-25

Decision: `launch_named_structural_lane`

Lane:

```text
v53_completion_first_hybrid_planner_controller
```

## Refinement

The user clarified the intended architecture:

```text
upper planner / MPPI / geometric route module
-> short local trajectory
-> virtual Level2 local-gate observation adapter
-> Level2 PPO tracker
-> roll/pitch/yaw/thrust
```

This is the preferred v53 structure.

## Why

Pure PPO has been forced to solve two different jobs at once:

- route planning: which gate/aperture/obstacle corridor to choose;
- body control: how to output stable attitude/thrust commands.

Level3 also has `sensor_range = 0.7`, so far-away geometry may be nominal and
near-gate geometry becomes reliable only late. A planner can slow down near this
range, observe the true local geometry, and generate a safer short trajectory.
The tracker can then focus on following that reference.

## Selected Tracker

Use this Level2 PPO checkpoint as the first tracker:

```text
lsy_drone_racing/control/checkpoints/level2_DR_latencyobs_middlemanuever/level2_DR_latencyobs_middlemanuever_final.ckpt
```

It uses `obstacle_heading_xy_v1`, hidden dim `256`, actor input dim `103`, and
outputs `[roll, pitch, yaw, thrust]`. It is chosen because it already has stable
Level2 flight/body-control behavior. It should be wrapped as a tracker, not used
as a full Level3 route planner.

## Implementation Meaning

The v53 controller should expose and log:

- current phase;
- target gate;
- reference position and velocity;
- reference tracking error;
- desired speed;
- gate-frame local position;
- aperture offset;
- virtual Level2 gate center/yaw used for the tracker;
- whether the controller is in pre-visibility, slowdown, align, cross, or
  recovery phase.

Direct planner action output remains allowed as a tracker baseline, but the
main experiment should not be another pure MPPI action-cost sweep.

## Guardrails

- Do not modify `config/level3.toml`.
- Do not use static seed replay.
- Do not count hybrid-controller success as PPO target success.
- Do not launch PPO BC/DAgger/fine-tuning until a later analysis packet and
  decision approve it.

## Next Action

Implement `lsy_drone_racing/control/level3_hybrid_planner_controller.py` around
the planner-reference-tracker split. Run builder/checker verification, then
smoke eval on seeds `101-105`, followed by dev eval on seeds `1-20` only if
smoke is clean.
