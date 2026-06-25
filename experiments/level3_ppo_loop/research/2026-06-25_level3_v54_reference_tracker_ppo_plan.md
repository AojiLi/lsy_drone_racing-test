# Level3 V54 Reference-Trajectory Tracker PPO Plan

Date: 2026-06-25

Lane:

```text
v54_reference_trajectory_tracker_ppo
```

## Core Idea

Do not ask PPO to solve the whole Level3 race at once.

Split the problem:

```text
upper planner:
  decides route, speed mode, visibility slowdown, aperture, and local trajectory

reference-tracker PPO:
  tracks the local reference trajectory and outputs roll / pitch / yaw / thrust
```

This replaces the failed v53 first attempt:

```text
planner reference -> virtual Level2 gate adapter -> existing Level2 PPO tracker
```

with a cleaner design:

```text
planner reference trajectory -> native reference-tracking PPO observation -> PPO action
```

## Why V53 Is Not Enough

The v53 smoke controller was action-finite but failed the behavior gate:

- seeds: `101-105`;
- success: `0%`;
- mean gates: `0.00`;
- finite actions: `100%`.

Trace evidence showed the controller could take off and approach gate 0, but it
could not reliably center and pass through the gate opening. This is expected:
the Level2 checkpoint was never trained to interpret planner references. Packing
planner intent into a synthetic gate is a brittle adapter.

## V54 Hypothesis

A PPO trained directly as a low-speed reference tracker should be easier to
learn than end-to-end Level3 racing.

The tracker does not decide the global route. It only learns:

- hover and hold position;
- track a local point;
- track a short local trajectory;
- match desired velocity;
- align with desired heading;
- stay centered in the current gate frame;
- avoid or slow near local obstacles.

The upper planner handles:

- using nominal gate positions when far away;
- slowing at approximately `0.7m-1.0m`;
- re-planning after true gate/obstacle geometry becomes visible;
- generating current point, pre-gate alignment point, safe aperture point, and
  post-gate recovery point;
- choosing a completion-first speed profile.

## Proposed Observation For Tracker PPO

The deployed tracker observation should be local and reference-centric.

Candidate fields:

```text
drone state:
  body-frame velocity
  angular velocity
  attitude / gravity direction
  last action
  short history

reference trajectory:
  current reference point relative to drone
  next reference point relative to drone
  lookahead reference point relative to drone
  desired velocity
  desired speed
  desired heading error
  reference progress / phase

gate frame:
  current gate local x/y/z error
  aperture y/z target
  pre-cross / cross / recovery phase one-hot

obstacles:
  nearest visible obstacle relative position
  obstacle clearance / distance
  obstacle detected mask
```

Initial network can stay conservative:

```text
2x256 Tanh MLP actor and critic
```

Do not start with GRU unless the non-recurrent tracker cannot hold/reference
track under observation delay. The tracker task is intentionally local enough
that 2x256 may be sufficient.

## Training Curriculum

Train the tracker in phases before full Level3 hard eval:

1. Hover and point-hold:
   random starts near a target point; reward reference position error,
   velocity damping, heading alignment, and low action jerk.
2. Point-to-point tracking:
   short straight segments at low speed.
3. Gate-aperture tracking:
   pre-gate point -> aperture point -> post-gate point, with fixed gates.
4. Visibility slowdown:
   train phases where planner target changes after the vehicle reaches
   `0.7m-1.0m` from the gate.
5. Obstacle-aware aperture:
   add visible obstacles and clearance penalties.
6. Full Level3 planner+tracker hard eval on unchanged `config/level3.toml`.

Training configs may be simpler curricula, but final acceptance always remains
hard eval on unchanged `config/level3.toml`.

## Reward Sketch

This reward is for the tracker, not the full race reward.

Suggested terms:

```text
- reference position error
- reference velocity error
- desired heading error
- gate local y/z centering near pre-cross and cross phases
- excessive closing speed near gate plane
- obstacle clearance penalty
- action magnitude / action delta
- crash penalty
- waypoint or phase completion bonus
```

Do not reward global race progress inside the tracker-only pretraining phase.
The purpose is to create a stable low-level follower.

## Acceptance Gates

Before any long Level3 run:

1. Builder/checker implementation gate passes.
2. Tracker smoke shows finite actions and stable hover/point tracking.
3. Gate-aperture smoke passes nonzero gate progress on deterministic mini tasks.
4. Planner+tracker smoke on Level3 seeds `101-105` shows at least nonzero first
   gate progress before dev `1-20`.

Do not promote to full validation if `101-105` stays at `0.00` mean gates.

## Boundary

- Do not edit `config/level3.toml`.
- Do not count tracker curriculum success as final Level3 success.
- Do not record hybrid/controller success as PPO end-to-end Level3 best unless
  the deployed action path and acceptance criteria are explicitly recorded.
- Do not continue v53 virtual Level2-gate adapter as the main route unless v54
  implementation is blocked.
