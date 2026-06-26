# V59 Reference Tracker With Local Safety Reflex Plan

Status: proposal recorded, no training launched.

## Motivation

The planner+tracker architecture should not force the bottom PPO to solve the
whole Level3 route. The upper planner decides where to go, when to slow down,
and which short reference horizon should be followed. The bottom PPO should be a
strong local servo.

However, planner smoke has repeatedly shown contact near gates or obstacles. A
pure tracker can be brittle if the reference is slightly wrong or if the drone
drifts near a frame. The next reasonable extension is a weak local safety
reflex:

```text
planner: route, slowdown, short reference horizon
tracker: follow the concrete reference command
safety reflex: small correction only near collision margins
```

## Design

The tracker must keep reference following as the primary objective. It should
not become a second autonomous gate-passing policy.

Primary command inputs remain:

- current reference point;
- next reference point;
- lookahead reference point;
- desired velocity;
- desired speed;
- desired heading;
- optional waypoint masks such as through, brake_or_hold, slow_through, recover.

Allowed lightweight safety inputs:

- nearest visible obstacle relative position;
- obstacle distance;
- obstacle detected flag;
- optional gate-frame clearance or nearest-frame direction only after evidence
  shows obstacle-only features are insufficient and builder/checker approves the
  observation-layout change.

Avoid these as tracker-reflex inputs:

- full target-gate semantics;
- gate progress;
- gate pass phase;
- finish state;
- stage progress;
- any route-level signal that makes the PPO decide the race strategy.

## Reward Rule

Use local tracking rewards, not Level3 race rewards.

Recommended weighting:

```text
80-90%: position/horizon tracking, velocity or speed tracking, heading tracking,
        braking/hold behavior when commanded, action smoothness
10-20%: crash, near-obstacle, near-frame, or clearance penalties, active mainly
        inside a safety margin
```

Do not add:

- gate_pass_bonus;
- finish_bonus;
- race progress bonus;
- stage progress bonus;
- reward terms that encourage the tracker to ignore the planner and choose a
  gate strategy itself.

## Current Code Audit

The current tracker implementation already has a useful starting point:

- `ReferenceFrame` includes `obstacle_relative`, `obstacle_distance`, and
  `obstacle_detected`;
- `ReferenceTrackerObservation.build()` includes those obstacle fields in the
  actor observation;
- `ReferenceTrackerReward` supports `obstacle_margin`, `obstacle_coef`, and
  crash penalties;
- v58 semantic layout already keeps future references, desired speed/velocity,
  desired heading, and waypoint masks visible.

Therefore, v59 should first try existing obstacle observation and safety reward
support before adding new observation fields.

## Acceptance Shape

V59 is useful only if it improves safety without destroying reference tracking:

- position and speed tracking do not regress beyond the v58 baseline;
- action delta remains bounded;
- collision or near-collision counts drop on held-out planner-like references;
- if planner smoke is used, unchanged `config/level3.toml` is verified;
- no gate-pass, finish, race-progress, or stage-progress reward is introduced.

## Next Action

Do not launch v59 training yet. First run the bounded v58 semantic
planner-reference preflight and stage evaluation. If v58 still shows contact
despite continuous, trackable references, launch a builder/checker-gated v59
support packet that audits existing obstacle features and adds only the minimal
safety metric or feature needed.
