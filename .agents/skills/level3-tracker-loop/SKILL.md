---
name: level3-tracker-loop
description: Use when training, evaluating, tuning, or analyzing the v54 Level3 low-level PPO reference tracker as a trajectory-following controller, before planner integration. Use for tracker qualification curricula such as hover, point hold, point reach, straight-line tracking, L-shaped tracking, curved trajectory tracking, braking-to-point, heading tracking, multi-point reference following, gate-aperture reference following, and deciding whether the tracker is ready for a planner-driven Level3 run. Use this instead of level3-ppo-loop when the question is about proving the bottom PPO can accurately, smoothly, and stably follow reference points/trajectories rather than directly optimizing Level3 gate-pass success.
---

# Level3 Tracker Loop

Use this workflow for the v54 low-level PPO tracker. The tracker is not the
global racer. Its first job is to behave like a reliable flying base:

```text
reference trajectory -> PPO tracker -> roll / pitch / yaw / thrust
```

Planner integration is allowed only after the tracker proves it can follow
short reference trajectories without overshooting, crashing, or producing
aggressive actions.

## Contract

- Target final race config remains unchanged: `config/level3.toml`.
- Tracker source files:
  - `lsy_drone_racing/control/level3_reference_tracker.py`;
  - `lsy_drone_racing/control/train_level3_reference_tracker_ppo.py`;
  - `lsy_drone_racing/control/level3_reference_tracker_controller.py`;
  - `scripts/check_level3_reference_tracker_smoke.py`.
- State file remains:
  `experiments/level3_ppo_loop/state.json`.
- W&B project remains: `ADR-PPO-Racing-Level3`.
- Current v54 hold packet:
  `experiments/level3_ppo_loop/decisions/2026-06-25_v54_reference_tracker_hold_long_training.md`.
- Current v54 long-training prep analysis:
  `experiments/level3_ppo_loop/analysis/2026-06-25_v54_reference_tracker_long_training_prep.md`.
- Current v54 finding: do not launch long Level3 training until the tracker
  passes qualification tasks and strict smoke. The last prep had finite actions
  and first-gate progress but `0/20` gate-0 passes on seeds `101-120`.

## Core Principle

Separate the two problems:

```text
planner quality:
  can the upper planner generate safe, low-speed, visible-geometry references?

tracker quality:
  can the PPO follow reference points and trajectories precisely and smoothly?
```

Do not use Level3 gate pass as the first tracker learning exam. Use gate pass as
an integration test after the tracker passes reference-following exams.

## Qualification Ladder

Train and evaluate in this order. Do not skip directly to full Level3 unless a
packet explains why the lower rungs are already proven.

1. `hover`
   - hold near a fixed target;
   - prioritize survival, low velocity, low action delta, and final position
     error.
2. `point_hold`
   - reach a point and stay near it;
   - require braking instead of flying through the target.
3. `point_reach`
   - travel from A to B at low speed;
   - measure final error, overshoot, time-to-target, and crash rate.
4. `line_tracking`
   - follow a straight short trajectory with desired velocity;
   - measure cross-track error and speed error.
5. `brake_to_point`
   - approach a point and reduce speed before arrival;
   - reject policies that only get close by overshooting.
6. `heading_tracking`
   - align desired heading while moving or hovering;
   - measure heading error without allowing large attitude commands.
7. `multi_point_reference`
   - follow multiple reference points with smooth switching;
   - measure jerk/action-delta and accumulated tracking error.
8. `l_shape_tracking`
   - follow a simple L-shaped route;
   - require stable turning without large overshoot.
9. `curve_tracking`
   - follow a small smooth curve;
   - require low cross-track error and no oscillation.
10. `gate_aperture_reference`
    - follow pre-gate -> aperture -> post-gate reference points;
    - this is still a tracker exam, not full Level3 racing.
11. `planner_integration_smoke`
    - run unchanged `config/level3.toml` with the upper planner and tracker.

## Metrics

Every tracker qualification analysis must report the relevant subset of:

- mean and median position error;
- final position error;
- cross-track error for line/L/curve tasks;
- desired velocity error;
- terminal speed near target;
- overshoot distance;
- heading error;
- crash / termination / timeout rate;
- mean action norm;
- action delta / smoothness;
- finite action and finite observation checks;
- W&B run URL;
- checkpoint path;
- exact task command and seed range.

For planner integration smoke, additionally report:

- nonzero first-gate progress count;
- gate-0 pass count;
- early termination count;
- `config/level3.toml` unchanged check.

## Promotion Gates

Do not approve planner-driven long Level3 training until all are true:

- tracker tasks are checkpoint-backed and action-finite;
- hover/point/line tasks show low final error and no systematic crash;
- multi-point/L/curve tasks show bounded overshoot and smooth action changes;
- braking task shows low terminal speed near the target;
- gate-aperture reference task demonstrates crossing or phase completion in the
  tracker-specific mini task;
- planner integration smoke on unchanged `config/level3.toml` seeds at least
  `101-120` has majority first-gate progress and at least one gate-0 pass.

If these fail, write a hold packet. Do not give a fake long-training command.

## Workflow

1. Read, in order:
   - `AGENTS.md`;
   - this skill;
   - `experiments/level3_ppo_loop/state.json`;
   - the latest v54 analysis and decision packet.
2. Identify the next missing qualification rung. Prefer the lowest unproven
   tracker skill over a full Level3 run.
3. If code or training semantics must change, use builder/checker:
   - builder implements the smallest change;
   - checker is read-only and verifies commands, semantics, and unchanged
     `config/level3.toml`;
   - main agent decides after checker, never builder.
4. Run bounded W&B-tracked training. This is qualification, not long training.
5. Run task-specific evaluation/smoke before any planner smoke.
6. Write an analysis packet under `experiments/level3_ppo_loop/analysis/`.
7. Write a main decision packet under `experiments/level3_ppo_loop/decisions/`
   choosing one of:
   `hold_for_more_analysis`, `continue_same_hypothesis`,
   `change_tracker_curriculum_or_reward`, `promote_to_planner_integration`, or
   `approve_manual_long_training_command`.
8. Write a plain Chinese reader note under `drone_notes/level3_loops/`.
9. Update `state.json`.
10. Commit intended small files and push to `aojili-test/main`.

## Training Guidance

- Prefer a dedicated tracker qualification script or task mode over direct
  Level3 reward tuning.
- Keep training chunks bounded until qualification metrics improve.
- Use W&B for live PPO metrics and tracker diagnostics.
- Keep generated checkpoints, smoke JSONs, W&B directories, logs, caches, and
  trajectory dumps out of git.
- Do not record tracker qualification success as final Level3 success.
- Do not modify `config/level3.toml`.

## Common Next Move

Given the current state, the next useful lane is:

```text
v55_tracker_qualification_curriculum
```

Its first implementation target should add task support and evaluation metrics
for:

```text
point_hold
point_reach
line_tracking
brake_to_point
multi_point_reference
l_shape_tracking
curve_tracking
gate_aperture_reference
```

The first acceptance target is not a Level3 success rate. It is evidence that
the tracker can follow references accurately enough for an upper planner to be
meaningful.
