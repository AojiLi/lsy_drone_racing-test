---
name: level3-mppi-loop
description: Use when implementing, evaluating, tuning, or analyzing the Level3 MPPI oracle/teacher loop for drone racing on unchanged config/level3.toml, including MPPI controller work, non-PPO controller evaluation, hard-eval reports, and teacher-data gating for later PPO imitation. Use instead of level3-ppo-loop when the task is about MPPI, sampling-based control, oracle controllers, teacher trajectories, BC/DAgger data from MPPI, or checking whether MPPI can pass Level3 before PPO training.
---

# Level3 MPPI / Non-PPO Controller Loop

Use this workflow for the separate MPPI oracle/teacher lane and for
completion-first non-PPO Level3 controller work. This skill is not for ordinary
PPO reward tuning or PPO training loops; use `$level3-ppo-loop` for PPO-only
work.

## Contract

- Target config: `config/level3.toml`.
- Racing target gate: success rate `>= 0.60` and mean successful time `<= 7.0s`.
- Current completion-first lane: `v53_completion_first_hybrid_planner_controller`.
- Completion-first screen: prioritize `>= 0.60` success on unchanged
  `config/level3.toml`; `15s-20s` successful time is acceptable as an
  intermediate milestone if the built-in 30s timeout permits it.
- Preferred v53 architecture: upper planner/MPPI/geometric route module
  generates a short reference trajectory; PPO or a low-level tracker follows
  the trajectory and outputs `[roll, pitch, yaw, thrust]`.
- Previous MPPI lane: `v52_mppi_oracle_teacher_level3`.
- Current decision packet:
  `experiments/level3_ppo_loop/decisions/2026-06-25_user_approves_completion_first_hybrid_controller.md`.
- Current research packet:
  `experiments/level3_ppo_loop/research/2026-06-25_level3_v53_completion_first_hybrid_controller_plan.md`.
- Current state file remains:
  `experiments/level3_ppo_loop/state.json`.
- MPPI-only success is controller/oracle evidence. Do not record it as PPO
  target success.

## Hard Boundaries

- Never edit `config/level3.toml` geometry, gates, obstacles, randomization, or
  validation seed split to make the task easier.
- MPPI, planner, or hybrid state-machine controllers may output
  `[roll, pitch, yaw, thrust]` only inside the approved non-PPO controller lane.
- Do not mix MPPI action output, safety shields, fallback controllers, or
  static seed replay into PPO lanes without a new explicit packet.
- Do not launch PPO BC, DAgger, or fine-tuning until an MPPI analysis packet
  shows useful hard-eval evidence and a main-agent decision explicitly opens
  teacher-data generation.
- Do not commit bulky generated datasets, W&B directories, logs, checkpoints,
  caches, or full trajectory dumps unless the user explicitly asks.

## Source Of Truth

Before acting, read:

1. `AGENTS.md`;
2. this skill;
3. `experiments/level3_ppo_loop/state.json`;
4. the v52 decision packet;
5. the v52 research packet.

If these conflict, `config/level3.toml` immutability and the latest state/decision
packet win.

## Workflow

1. **Implementation/preflight**
   - Add or update the smallest useful MPPI oracle controller, expected path:
     `lsy_drone_racing/control/mppi_level3_oracle.py` or
     `lsy_drone_racing/control/level3_hybrid_planner_controller.py`.
   - Add or adapt a non-PPO controller evaluator, expected path:
     `scripts/evaluate_level3_controller.py`.
   - Keep metrics aligned with the existing hard evaluator: success, mean
     successful time, crash, timeout, mean gates, termination reason, failure
     gate, and failure taxonomy.

2. **Builder/checker gate**
   - Use builder for code changes and checker for read-only verification.
   - Do not let builder self-approve.
   - Checker must verify `git diff --check`, Python compile checks, finite
     actions, a tiny smoke eval if feasible, and unchanged `config/level3.toml`.

3. **Smoke eval**
   - Run only 5-10 seeds first.
   - Require finite `[roll, pitch, yaw, thrust]`, no NaNs, no evaluator crash,
     sane termination logging, and no Level3 config diff.

4. **Development eval**
   - Use a small non-final seed set.
   - Tune MPPI cost/model/horizon only if smoke is clean.
   - Compare mean gates and crash against the PPO frontier.

5. **Validation hard eval**
   - Run `validation_unseen 101-200` on unchanged `config/level3.toml`.
   - Compare against current PPO frontier: `21%` success, `1.66` mean gates,
     `79%` crash, `7.578s` mean successful time.

6. **Decision**
   - Write an analysis packet under `experiments/level3_ppo_loop/analysis/`.
   - Choose exactly one next action:
     `hold_for_more_analysis`, `continue_same_hypothesis`,
     `launch_named_structural_lane`, or `start_teacher_dataset_generation`.
   - Write a plain Chinese reader note under `drone_notes/level3_loops/`.
   - Update state, commit intended small files, and push to `aojili-test/main`.

## Completion-First Hybrid Defaults

The first v53 controller should be slower and more explicit than pure PPO:

- takeoff/stabilize;
- cruise to a pre-gate waypoint;
- slow down near local visibility range, especially around the `0.7m`
  `level3.toml` sensor range where true gate/obstacle poses become visible;
- replan a local `1s-2s` reference trajectory after the gate/obstacle is
  observed;
- align in the active gate frame;
- choose an obstacle-aware aperture point;
- let PPO or a low-level tracker follow reference position/velocity/phase;
- cross the gate only after alignment and speed reduction;
- recover after crossing before accelerating to the next gate.

Direct action output is allowed in this lane for controller/tracker baselines,
but the preferred structure is planner trajectory -> tracker -> action. Keep it
separate from PPO metrics.

## MPPI Design Defaults

Start conservative, then scale:

- action: `[roll, pitch, yaw, thrust]`;
- horizon: about `0.8s-1.5s`;
- control rate: respect Level3 environment frequency;
- samples: start small for smoke, then scale after finite-action checks;
- warm start: shift previous best sequence forward;
- objective priority: correct gate order and survival first, speed second.

Score candidate sequences with terms for:

- active gate progress and correct gate order;
- gate aperture/centerline error;
- obstacle clearance;
- bounds/contact risk;
- tilt and command tilt;
- action smoothness;
- finish bonus and time cost.

## Promotion Rules

- If MPPI reaches `>=60%` success and `<=7.0s`, treat it as a viable Level3
  controller candidate and high-value PPO teacher.
- If MPPI reaches `>=40%` success or clearly expands solved-seed coverage
  beyond PPO, open a follow-up teacher-data lane.
- If MPPI is fast enough only offline, keep it as an offline data generator.
- If MPPI stays near the PPO plateau, improve MPPI model/cost/horizon before
  any PPO imitation work.

## Teacher Data Gate

Only generate PPO imitation data after a written MPPI analysis packet and
main-agent decision allow it.

When allowed, dataset rows should include:

- actor observation;
- MPPI action `[roll, pitch, yaw, thrust]`;
- normalized PPO action if relevant;
- seed, target gate, gate progress, success flag, termination reason;
- optional MPPI diagnostics such as best cost, cost quantiles, and selected
  action sequence summary.

Generated datasets are artifacts. Keep them out of git by default.
