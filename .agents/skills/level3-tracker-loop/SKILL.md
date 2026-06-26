---
name: level3-tracker-loop
description: Use when training, evaluating, tuning, or analyzing the v54/v55 Level3 low-level PPO reference tracker as a trajectory-following controller, before planner integration. Use for tracker qualification curricula such as hover, point hold, point reach, straight-line tracking, L-shaped tracking, curved trajectory tracking, braking-to-point, heading tracking, multi-point reference following, optional gate-aperture diagnostics, and deciding whether the tracker is ready for a planner-driven Level3 run. Use this instead of level3-ppo-loop when the question is about proving the bottom PPO can accurately, smoothly, and stably follow reference points/trajectories rather than directly optimizing Level3 gate-pass success.
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

For v58 and later, "reference following" means following a semantic short
trajectory, not blindly chasing a single point. The planner must tell the
tracker both geometry and intent:

```text
reference_point
desired_velocity
desired_speed
desired_heading
waypoint_type / stop_signal / brake_mask
next_point
lookahead_point
```

The tracker must learn distinct behaviors:

```text
through: keep moving smoothly through the point
brake_or_hold: slow to about 0.0-0.1 m/s and stabilize/alignment-hold
slow_through: do not stop dead, but cross at about 0.25-0.35 m/s
recover: resume speed gradually after the constrained segment
```

Do not reduce v58 to ordinary point chasing. If every reference point has the
same semantics, the tracker can learn to rush through all points and still fail
Level3 by overshooting, failing to brake, or contacting near the gate plane.

Planner integration smoke should start with the deterministic
`GeometricSlowGatePlanner` in
`lsy_drone_racing/control/level3_reference_tracker.py`, not MPPI/MPC. It is a
conservative five-phase state machine: cruise, slowdown, align, cross, recover.
It outputs only short-horizon reference points, desired speed, and heading; the
PPO tracker remains the only action source.

## Research Reference

When changing tracker observations, reward terms, qualification tasks, PPO
training schedule, or planner-integration gates, first read:

```text
.agents/skills/level3-tracker-loop/references/tracker-ppo-training.md
```

That file records the source-backed tracker-training pattern from DATT,
OmniDrones, safe-control-gym, quadrotor racing papers, and PPO implementation
notes. Keep `SKILL.md` procedural and update the reference file when new durable
evidence changes how tracker PPO should be trained.

Current v55 training-environment memory:

```text
experiments/level3_ppo_loop/research/2026-06-25_v55_tracker_training_environment_memory.md
```

Use it when deciding whether tracker training should run in free space, a
gate-aperture mini environment, or unchanged `config/level3.toml` smoke.

Current v55 training-budget research:

```text
experiments/level3_ppo_loop/research/2026-06-25_v55_tracker_training_budget_research.md
```

Use it when deciding whether a tracker stage has been trained long enough,
whether to extend the same stage, or whether a failure justifies changing
reward, curriculum, observation, PPO structure, or planner integration.

Current v55 machine-readable completion gates:

```text
experiments/level3_ppo_loop/tracker_qualification_gates.json
```

Use this gate spec with:

```bash
pixi run -e tests python scripts/check_level3_tracker_stage_gate.py \
  --stage <stage_id> \
  --metrics-json <stage_eval_metrics.json>
```

Generate the stage metrics JSON with:

```bash
pixi run -e gpu python scripts/evaluate_level3_tracker_stage.py \
  --stage <stage_id> \
  --checkpoint <tracker_checkpoint.ckpt> \
  --output <stage_eval_metrics.json>
```

When starting any stage after `hover`, add `--require-prerequisites` and pass a
history JSON that marks prior stages as passed. The stage checker must pass
before the next stage is unlocked.

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
10. `zigzag_or_lemniscate_tracking`
    - follow sharper but still short held-out curves;
    - require low tracking error without unstable corrective actions.
11. `semantic_planner_reference`
    - follow planner-like semantic reference sequences;
    - distinguish through, brake/hold, slow-through, and recover behavior.
12. `planner_integration_smoke`
    - run unchanged `config/level3.toml` with `GeometricSlowGatePlanner` and
      the PPO tracker.

Optional diagnostic: `gate_aperture_reference` may be used to inspect whether a
planner-generated pre-gate -> aperture -> post-gate reference is trackable, but
it is not a required tracker-training stage. The planner owns aperture crossing
semantics; the bottom PPO owns reference tracking.

After v57a, the next tracker lane should be a named semantic-reference stage,
not a repeat of the generic ladder. Use:

```text
v58_tracker_semantic_planner_reference_training
```

This stage should train on planner-like short trajectories with waypoint
intent. Minimal reference families:

- far cruise `through` points with target speed about `0.6-1.0m/s`;
- pre-gate align `brake_or_hold` points with target speed about `0.0-0.1m/s`;
- aperture `slow_through` points with target speed about `0.25-0.35m/s`;
- post-gate `through/recover` points that restore speed gradually;
- mixed sequences such as
  `through -> brake_or_hold -> slow_through -> recover`.

The observation, reward, and evaluation must make the semantic intent visible
or measurable. If the current actor observation cannot represent waypoint type,
stop/hold intent, or brake intent, v58 must include a small observation-layout
change with builder/checker approval before long training.

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

For semantic planner-like reference training, additionally report:

- per-waypoint-type position and velocity error;
- brake/hold terminal speed and dwell stability;
- slow-through speed error through the aperture-like segment;
- overshoot after brake/hold points;
- velocity reduction from approach speed to commanded slow-through speed;
- wrong-semantics failures, such as rushing through brake points or stopping
  dead at slow-through points;
- waypoint-type confusion rates if an explicit classifier/one-hot interface is
  used.

For planner integration smoke, additionally report:

- nonzero first-gate progress count;
- gate-0 pass count;
- early termination count;
- `config/level3.toml` unchanged check.

## Promotion Gates

Each stage has a concrete completion gate in
`experiments/level3_ppo_loop/tracker_qualification_gates.json`. The loop may
continue to the next stage only after `scripts/check_level3_tracker_stage_gate.py`
returns success for the current stage. Missing metrics fail closed.

Do not approve planner-driven long Level3 training until all are true:

- tracker tasks are checkpoint-backed and action-finite;
- hover/point/line tasks show low final error and no systematic crash;
- multi-point/L/curve tasks show bounded overshoot and smooth action changes;
- braking task shows low terminal speed near the target;
- the first 10 free-space tracker stages through `zigzag_or_lemniscate_tracking`
  are checkpoint-backed and passed;
- planner integration smoke on unchanged `config/level3.toml` seeds at least
  `101-120` has majority first-gate progress and at least one gate-0 pass.

If these fail, write a hold packet. Do not give a fake long-training command.

## Workflow

1. Read, in order:
   - `AGENTS.md`;
   - this skill;
   - `.agents/skills/level3-tracker-loop/references/tracker-ppo-training.md`
     when changing tracker observation, reward, curriculum, training schedule,
     or promotion gates;
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

## Autonomous Required-Stage Goal Protocol

When the user launches a `/goal` for the full tracker ladder, run exactly one
stage at a time:

```text
train current stage
-> evaluate current stage with scripts/evaluate_level3_tracker_stage.py
-> check current stage with scripts/check_level3_tracker_stage_gate.py
-> if pass, update state and unlock next stage
-> if fail, analyze, change the smallest useful thing, and retry the same stage
```

The current required stage follows the `next_stage` chain in
`experiments/level3_ppo_loop/tracker_qualification_gates.json`, ignoring stages
marked `optional_diagnostic`. If the first 10 tracker stages are passed, the next
required stage is `planner_integration_smoke`, not `gate_aperture_reference`.

On a failed stage gate, spawn exactly three analysis subagents before changing
training structure or reward:

- `tracker_eval_metrics`: inspect the stage metrics JSON, gate failures, episode
  rows, crash/termination patterns, overshoot, terminal speed, and action
  smoothness.
- `tracker_wandb_ppo`: inspect W&B curves for the stage run: episode return,
  tracker reward components, policy loss, value loss, entropy, clip fraction,
  and signs of undertraining or PPO instability.
- `tracker_structure_research`: inspect whether the fix should be more
  training time, reward numbers, curriculum difficulty, observation features,
  PPO hyperparameters, or a small code/config correction. Use local evidence
  first and external research only when it materially changes the decision.

The main agent must synthesize those reviews into a decision packet under
`experiments/level3_ppo_loop/decisions/` before retrying. Allowed decisions are:
`continue_same_stage_more_steps`, `change_tracker_reward_numbers`,
`change_tracker_curriculum_or_eval`, `launch_tracker_structural_fix`, or
`hold_for_user_review`.

If the decision changes observation layout, reward semantics, trainer behavior,
evaluator semantics, controller behavior, or loop orchestration, use the
builder/checker gate before training again. The checker must be read-only and
must verify unchanged `config/level3.toml`.

Do not approve planner-driven Level3 long training until the required tracker
ladder through `zigzag_or_lemniscate_tracking` is passed and
`planner_integration_smoke` passes on unchanged `config/level3.toml`.

## Long-Stage Training Policy

Short smoke runs are only plumbing checks. They verify that the trainer,
checkpoint writer, W&B logging, evaluator, and gate checker can run. They are
not enough evidence to decide that PPO did or did not learn a tracker skill.

For each learning stage:

1. Run a short preflight smoke using the stage's
   `training_budget.preflight_smoke_timesteps` from
   `experiments/level3_ppo_loop/tracker_qualification_gates.json`.
2. If smoke fails due to NaNs, non-finite actions/observations, trainer or
   evaluator errors, invalid checkpoint metadata, or `config/level3.toml`
   mutation, treat it as a semantic/plumbing failure and use builder/checker.
3. If smoke is clean, run a bounded stage-maturation chunk with explicit
   `--total-timesteps`, W&B enabled, and `--checkpoint-interval` from the stage
   `training_budget`.
4. Evaluate milestone checkpoints, not only the final checkpoint.
5. Judge stage completion only from checkpoint-backed milestone evaluation plus
   the stage gate checker.

Do not mark a learning stage failed based only on `<=100000` timesteps unless
the failure is a semantic/plumbing failure such as NaNs, non-finite actions,
broken evaluation, invalid checkpoint metadata, or `config/level3.toml`
changes. Tiny runs can reject broken code; they cannot reject PPO learning.

Default stage-maturation budgets are machine-readable in the gate spec:

```text
hover: 1M
point_hold: 2M
point_reach, brake_to_point, heading_tracking: 4M
line_tracking: 5M
multi_point_reference, l_shape_tracking: 8M
curve_tracking: 10M
zigzag_or_lemniscate_tracking: 12M
semantic_planner_reference: 8M default, 20M research extension
planner_integration_smoke: no new training, evaluate only
gate_aperture_reference: optional diagnostic only, no default maturation
```

Tracker learning chunks must use vectorized environments. The single-env
trainer path is now only for tiny debug/smoke checks. The default maturation
rollout geometry follows the successful Level2/Level3 PPO precedent:

```text
1024 envs x 32 steps = 32768 samples/update
```

If W&B/milestone analysis suggests this has too little temporal credit horizon
for a tracker stage, a main-agent decision packet may switch that stage to the
known longer-rollout variant:

```text
256 envs x 128 steps = 32768 samples/update
```

These are bounded chunks, not infinite training approval. If a stage still
fails after its default maturation chunk, run the three failure-review subagents
before changing reward, curriculum, PPO hyperparameters, network size, or the
budget. At least one review must explicitly answer whether the failure is more
consistent with undertraining, bad reward/metrics, bad curriculum difficulty,
PPO instability, or insufficient observation/control authority.

When changing the budget table or rejecting a stage as undertrained, create a
research/budget packet under `experiments/level3_ppo_loop/research/` using:

- local W&B and milestone curves;
- local Level2/Level3 step-curve experience;
- papers and GitHub examples for quadrotor tracking or drone racing PPO;
- hardware/runtime constraints.

The main agent, not the research subagent, owns the final budget decision.

## Training Guidance

- Prefer a dedicated tracker qualification script or task mode over direct
  Level3 reward tuning.
- Observation should include local/body-frame reference error and a short future
  reference horizon, plus desired velocity/speed, heading/yaw error, drone
  velocity/attitude/body-rate features, and previous action/history where
  available.
- Keep reward local to tracker behavior: tracking error, velocity error,
  heading error, braking terminal speed, overshoot, action smoothness,
  uprightness/spin, and crash/timeout. Do not use global race progress as the
  first tracker-learning reward.
- Increase reference difficulty in stages: fixed/easy references first, then
  randomized starts/endpoints/speeds/curvature, then disturbances/latency/domain
  randomization after nominal tracking works.
- During analysis, inspect PPO diagnostics such as approximate KL, clip
  fraction, entropy/action std, value loss, explained variance, and reward
  scale relative to value clipping.
- Keep training chunks bounded but explicit. The trainer default
  `--total-timesteps 4096` is only a smoke value; every real learning run must
  set `--total-timesteps` and `--checkpoint-interval`.
- Use W&B for live PPO metrics and tracker diagnostics.
- Keep generated checkpoints, smoke JSONs, W&B directories, logs, caches, and
  trajectory dumps out of git.
- Do not record tracker qualification success as final Level3 success.
- Do not modify `config/level3.toml`.

## Common Next Move

Given the current state, the next useful lane is:

```text
v58_tracker_semantic_planner_reference_training
```

The v55 qualification ladder is already useful evidence that the tracker can
follow basic free-space references, but v57/v57a showed that Level3 failure now
depends on planner-like reference semantics:

```text
the tracker must know whether a waypoint is a pass-through point, a braking /
hold point, or a low-speed through point.
```

The first v58 implementation target should add task support, observation
features if needed, reward terms, and evaluation metrics for semantic
planner-like reference segments. Acceptance is not Level3 success rate. It is
evidence that the tracker can execute `through`, `brake_or_hold`,
`slow_through`, and `recover` commands with bounded tracking error, low
overshoot, and correct speed behavior.

As of the v55 architecture clarification, `gate_aperture_reference` is no longer
part of the required ladder. Do not continue reward-shaped gate-aperture PPO
training by default; use the zigzag-qualified tracker in planner integration
smoke and diagnose failures as either planner-reference design problems or
tracker reference-following gaps.

The first planner smoke implementation is `GeometricSlowGatePlanner`: a slow
deterministic gate-frame planner with phase hysteresis, near-gate slowdown,
pre-gate alignment, pre/aperture/post/recovery references, and a simple visible
obstacle waypoint offset. If planner smoke fails, inspect the generated
references before adding MPPI or retraining the tracker.

As of v57a, the cross-entry reference discontinuity has been reduced from about
`0.74m` to `0.28m`, but gate0 pass/contact did not improve and phase4 speed
remained too high. That result is the trigger for v58 semantic tracker
training: train the bottom policy to brake, hold, slow-through, and recover
according to planner intent.

For the next planner-only gate-front tuning lane, use the repo skill:

```text
.agents/skills/level3-geometric-planner-loop/SKILL.md
```

That skill owns `v56_geometric_gate_crossing_tuning_loop`: fixed seeds
`101-120`, 500-step trace smoke, no PPO training, no checkpoint changes, no
`config/level3.toml` edits, and task metrics for align stabilization, cross
slowdown, near-plane backout, and recover-after-real-gate-switch behavior.
