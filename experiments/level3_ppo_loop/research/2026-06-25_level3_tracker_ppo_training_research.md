# Level3 Tracker PPO Training Research

Date: 2026-06-25

Purpose: update the Level3 tracker loop with source-backed guidance for training
a low-level PPO controller that follows reference points and short trajectories
before planner-driven Level3 integration.

## Question

How should the bottom PPO be trained if its job is not to solve Level3 directly,
but to follow references from an upper planner?

## Short Answer

Train the PPO as a local reference tracker first. It should learn to follow
hover, point, line, braking, curved, and gate-aperture references with low
tracking error, low overshoot, low terminal speed, and smooth actions. Only
after that should unchanged `config/level3.toml` be used as planner-integration
smoke.

This means the next loop should not ask "does this checkpoint finish Level3?"
as the first exam. It should ask "can this checkpoint accurately and smoothly
follow reference trajectories that a planner can compose into Level3 behavior?"

## Sources Reviewed

- DATT, CoRL 2023 / PMLR:
  https://proceedings.mlr.press/v229/huang23a.html
- DATT official implementation:
  https://github.com/KevinHuang8/DATT
- OmniDrones Track task:
  https://omnidrones.readthedocs.io/en/latest/tasks/single/Track.html
- OmniDrones FlyThrough task:
  https://omnidrones.readthedocs.io/en/latest/tasks/single/FlyThrough.html
- safe-control-gym quadrotor 3D tracking config:
  https://github.com/learnsyslab/safe-control-gym/blob/main/examples/rl/config_overrides/quadrotor_3D/quadrotor_3D_track.yaml
- Stable-Baselines3 PPO docs:
  https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html
- Reaching the Limit in Autonomous Racing:
  https://arxiv.org/abs/2310.10943
- RL vs geometric control trajectory-tracking benchmark:
  https://github.com/PratikKunapuli/rl-vs-gc
- PyFlyt waypoint task:
  https://github.com/jjshoots/PyFlyt

## Durable Findings

1. Use a short future reference horizon.

   Multiple tracker tasks condition the policy on future reference positions or
   receding reference windows. For our v55 tracker, the actor should see local
   or body-frame current error plus several future reference deltas, desired
   velocity/speed, desired heading, and previous action/history.

2. Keep the reward local to tracking quality.

   The tracker reward should optimize position/cross-track error, final error,
   desired-speed error, heading error, terminal speed near target, overshoot,
   action norm/action delta, uprightness/spin, crash, and timeout. Full-race
   progress reward belongs later, if at all, because it can reward moving
   forward while hiding inability to brake or align.

3. Train as a curriculum, not as one Level3 jump.

   The recommended ladder is:

   ```text
   hover
   point_hold
   point_reach
   brake_to_point
   line_tracking
   heading_tracking
   multi_point_reference
   l_shape_tracking
   curve_tracking
   zigzag_or_lemniscate_tracking
   gate_aperture_reference
   planner_integration_smoke
   ```

   Increase speed, curvature, randomization, latency, and disturbance only
   after the easier stage has stable held-out metrics.

4. Gate-aperture is a tracker mini task, not full Level3.

   Follow the separation used by OmniDrones-style tasks: reward distance to the
   plane and center/margin, then promote only on valid crossing through the
   aperture plus post-gate recovery. This directly targets the current symptom:
   v54 can create first-gate progress on many seeds but still has 0/20 gate-0
   passes in strict smoke.

5. Use PPO diagnostics as a gate, not only reward.

   For every bounded training run, inspect approximate KL, clip fraction,
   entropy/action standard deviation, value loss, explained variance, and
   reward scale relative to value clipping. Checkpoint milestone curves matter;
   final checkpoint is not assumed best.

6. Avoid premature GRU.

   Start with reference horizon and short history/action history. Add recurrent
   PPO only if the qualified tracker still shows a clear partial-observability
   failure after these features exist.

7. Do not make the planner a blind trajectory replay system.

   Racing-specific evidence warns that a pure trajectory interface can be
   brittle under mismatch. The planner should generate local, slow-safe
   references with margins and braking. The PPO tracker should remain
   feedback-driven and robust to small deviations.

## Skill Update

The tracker skill now points to:

```text
.agents/skills/level3-tracker-loop/references/tracker-ppo-training.md
```

Future agents must read that reference before changing tracker observation,
reward, curriculum, PPO schedule, or promotion gates.

## Next Recommended Work

Implement `v55_tracker_qualification_curriculum` as a research-backed tracker
qualification lane:

- add or verify the curriculum rungs listed above;
- log independent tracking metrics for every rung;
- require held-out references and checkpoint-backed evaluation;
- run strict planner-integration smoke on unchanged `config/level3.toml` only
  after mini-task gates pass;
- keep W&B logging in `ADR-PPO-Racing-Level3`;
- keep generated checkpoints, smoke JSON, W&B directories, logs, caches, and
  trajectory dumps out of git.

Long planner-driven Level3 training remains not approved until tracker
qualification and strict smoke pass.
