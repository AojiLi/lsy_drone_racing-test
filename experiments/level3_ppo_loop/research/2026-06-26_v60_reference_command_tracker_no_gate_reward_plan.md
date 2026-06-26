# V60 Reference Command Tracker With No Gate Reward Plan

Status: proposal recorded, no training launched.

## Why V58 Is Held

The user rejected the existing v58 framing because it can push the bottom PPO
toward learning gate-passing behavior. That is the wrong separation of
responsibilities.

The planner should decide where to go and when to slow down. The bottom tracker
should learn a generic low-level skill:

```text
given a short reference horizon + desired speed/velocity + desired heading,
follow it smoothly, brake when commanded, move slowly when commanded, and avoid
overshoot.
```

It should not receive gate-pass, aperture-crossing, finish, race-progress, or
stage-progress reward.

## V60 Objective

Replace the old v58 semantic-reference stage with:

```text
v60_reference_command_tracker_no_gate_reward
```

Canonical tracker task:

```text
reference_command_no_gate_reward
```

The task is free-space trajectory-command training, not gate training.
The clean actor observation layout is:

```text
level3_reference_tracker_command_v3
```

It intentionally removes gate, obstacle, and planner phase inputs.

## Input Interface

Primary actor inputs:

- own state;
- current reference point relative to drone;
- next reference point relative to drone;
- lookahead reference point relative to drone;
- desired velocity;
- desired speed;
- desired heading / heading error;
- optional generic command masks.
- last action;
- short history.

Forbidden actor inputs for the clean v60 baseline:

- gate-local position;
- aperture Y/Z;
- target-gate index or gate-pass state;
- obstacle relative position/distance/detected;
- planner phase one-hot.

Generic command intents:

- `pass_through`: continue through the point at commanded speed;
- `hold_or_brake`: slow to about `0.0-0.1m/s` and stabilize;
- `low_speed_through`: move through a constrained segment at about
  `0.25-0.35m/s`, without stopping dead;
- `recover_speed`: gradually restore speed.

These are not gate labels. They are generic motion commands.

## Reward Rule

Allowed reward terms:

- reference position / horizon tracking;
- desired velocity or desired speed tracking;
- desired heading tracking;
- low terminal speed and dwell stability when command is `hold_or_brake`;
- low but nonzero speed tracking when command is `low_speed_through`;
- overshoot penalty;
- action norm and action-delta smoothness;
- uprightness, spin/body-rate, crash/timeout penalties;
- small local safety penalty if needed later.

Forbidden reward terms:

- `gate_pass_bonus`;
- aperture-crossing bonus;
- finish bonus;
- race-progress bonus;
- stage-progress bonus;
- target-gate transition reward;
- any reward that lets the tracker treat planner reference as optional advice.

## Code/Loop Changes Recorded

- Added canonical task name `reference_command_no_gate_reward`.
- Kept old `semantic_planner_reference` and `semantic_reference` as aliases only.
- Replaced v2 waypoint type names with generic command names:
  `pass_through`, `hold_or_brake`, `low_speed_through`, `recover_speed`.
- Added clean command observation layout `level3_reference_tracker_command_v3`
  with `56` dimensions, down from `72` in semantic v2.
- Updated tracker qualification gates so the required stage after
  `zigzag_or_lemniscate_tracking` is `reference_command_no_gate_reward`.
- Kept the stage in free space on `config/level3_tracker_free_space.toml`.
- No training launched.
- `config/level3.toml` remains unchanged.

## Next Action

Run builder/checker validation for v60 support, then run only a bounded smoke.
Do not start long training until checker verifies:

- old v55/v1 checkpoint compatibility remains intact;
- v60 task uses `level3_reference_tracker_command_v3` intentionally;
- gate reward coefficients are zero in the intended v60 command;
- gate, obstacle, and phase features are absent from the v60 actor observation;
- `config/level3.toml` is unchanged;
- focused tests pass.
