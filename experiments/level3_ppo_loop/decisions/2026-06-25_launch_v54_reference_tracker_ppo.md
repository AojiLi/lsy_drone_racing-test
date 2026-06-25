# Decision: Launch V54 Reference-Trajectory Tracker PPO

Date: 2026-06-25

Decision: `launch_named_structural_lane`

Lane:

```text
v54_reference_trajectory_tracker_ppo
```

## Decision

Adopt the user-approved direction:

```text
far from gate:
  planner uses nominal gate position and flies slowly

near 0.7m-1.0m:
  planner slows down and waits for true gate/obstacle geometry

after true geometry is visible:
  planner creates a local reference trajectory:
    current point
    pre-gate alignment point
    safe aperture point
    post-gate recovery point

PPO tracker:
  follows this reference trajectory and outputs roll / pitch / yaw / thrust
```

The next step is not another v53 virtual-gate adapter tuning pass. The next step
is to implement and train a native reference-tracking PPO low-level controller.

## Rationale

The v53 smoke implementation proved the wiring can be action-finite, but the
existing Level2 PPO checkpoint is not a real reference tracker. It reached the
first-gate neighborhood but failed to center and convert through the opening.

This suggests the cleaner path is to train the bottom controller on the actual
task it will perform:

```text
given local reference trajectory + gate/obstacle errors,
stably output attitude commands that track it.
```

This is simpler than end-to-end Level3 PPO because the planner owns the global
route and the PPO owns only local tracking.

## Approved Implementation Scope

Implement v54 support through a builder/checker gate before training:

- a reference-trajectory generator for Level3-style local tasks;
- a tracker observation layout centered on reference error, desired velocity,
  desired heading, gate-frame error, obstacle distance, last action, and short
  history;
- a tracker reward focused on hover, low-speed reference tracking, heading
  alignment, gate aperture centering, obstacle clearance, and smooth actions;
- a tracker PPO training entrypoint or named loop support;
- an inference/controller path that combines the upper planner with the trained
  tracker;
- smoke checks for hover/point tracking, gate-aperture mini tasks, and Level3
  seeds `101-105`.

Initial tracker network:

```text
2x256 Tanh MLP
```

GRU is not the first move. Add GRU only if the local reference tracker shows a
clear memory/observation-delay failure after the MLP tracker is working.

## Not Approved

- Do not modify `config/level3.toml`.
- Do not count curriculum tracker success as final Level3 success.
- Do not record v54 as final target success until hard eval on unchanged
  `config/level3.toml` passes the accepted deployment path.
- Do not generate PPO teacher data from v53/v54 until planner+tracker smoke has
  meaningful Level3 gate progress.
- Do not continue v53 virtual Level2-gate adapter tuning as the primary route.

## Promotion Rules

Before dev `1-20`:

- finite actions;
- stable hover/point tracking smoke;
- nonzero gate-aperture mini-task progress;
- Level3 `101-105` smoke has nonzero first-gate progress.

Before validation `101-200`:

- dev `1-20` should show meaningful improvement over v53 smoke;
- no mutation of `config/level3.toml`;
- analysis packet and checker packet must be written.

## Source Packet

```text
experiments/level3_ppo_loop/research/2026-06-25_level3_v54_reference_tracker_ppo_plan.md
```
