# V52 Plan: MPPI Oracle And Teacher Dataset Loop

Status: approved structural plan draft after the user explicitly requested an
MPPI loop for Level3.

## Objective

Create a separate Level3 MPPI oracle loop before any new PPO training.

The first question is not whether PPO can learn immediately. The first question
is whether a sampling-based controller can solve the unchanged final target:

- hard eval on `config/level3.toml`;
- success rate `>= 60%`;
- mean successful time `<= 7.0s`;
- no Level3 track geometry, gate layout, obstacle layout, randomization, or
  validation seed split changes.

If MPPI can pass or clearly approach the target, use it to generate successful
trajectory/action data for PPO imitation and later PPO fine-tuning.

## Why MPPI

The current PPO family is plateaued around the `18%-21%` hard-eval success
range. v51 planner-guidance observation gave PPO extra route-intent features,
but it did not improve hard-eval success or mean gates. This suggests the
missing piece is not another small reward-number tweak, but a stronger
route/trajectory mechanism.

MPPI is appropriate because it can:

- sample future action sequences directly;
- score them with hard costs for gate progress, collision, obstacle clearance,
  bounds, tilt, smoothness, and finish time;
- handle non-smooth penalties better than purely gradient-based trajectory
  optimization;
- produce state-action demonstrations if it solves seeds that PPO cannot solve.

## Structural Boundary

This packet explicitly approves MPPI as an oracle/teacher loop. This is a new
structural lane and supersedes the previous "no planner actions" boundary only
for the MPPI oracle experiment described here.

Approved:

- implement an MPPI controller module for evaluation;
- let the MPPI controller output `roll/pitch/yaw/thrust` during MPPI oracle
  evaluation;
- run hard eval on unchanged `config/level3.toml`;
- generate successful demonstration datasets only after MPPI validation
  evidence is good enough.

Not approved:

- editing `config/level3.toml`;
- replaying validation or final seed-specific static routes;
- claiming PPO target success from MPPI-only results;
- launching PPO BC/DAgger/fine-tuning before MPPI oracle evidence is written;
- committing bulky generated datasets, W&B directories, logs, or checkpoints.

## Implementation Lane

Name:

```text
v52_mppi_oracle_teacher_level3
```

Minimum builder scope:

1. Add a Level3 MPPI oracle controller, for example
   `lsy_drone_racing/control/mppi_level3_oracle.py`.
2. Add or adapt an evaluator that can run non-PPO controllers without requiring
   a PPO checkpoint, for example `scripts/evaluate_level3_controller.py`.
3. Keep the evaluation metrics aligned with the existing hard evaluator:
   success, mean successful time, crash rate, timeout rate, mean gates,
   termination reason, failure gate, and failure taxonomy.
4. Add a small smoke command on a small seed set before full validation.
5. Add a dataset-generation mode only after the MPPI oracle passes the first
   meaningful hard-eval gate.

The builder/checker gate is required before any MPPI hard eval because this
touches inference action path and evaluator semantics.

## MPPI Controller Shape

Initial controller design:

```text
current obs
-> build local gate/obstacle objective
-> sample candidate action sequences over a short horizon
-> rollout with a simplified drone model or simulator-compatible dynamics
-> score by gate progress, aperture error, obstacle clearance, bounds, tilt,
   smoothness, and time
-> apply first action of the weighted/best sequence
-> repeat at 50 Hz
```

Initial practical settings should start conservative and then scale:

- action: `[roll, pitch, yaw, thrust]`;
- horizon: about `0.8s-1.5s`;
- samples: start small for smoke tests, then scale up;
- warm start: shift the previous best action sequence forward;
- objective priority: finish and gate order first, speed second.

## Evaluation Gates

Stage A: implementation smoke

- run on a tiny seed set, for example 5-10 seeds;
- require no NaNs, finite actions, no evaluator crashes, and unchanged
  `config/level3.toml`.

Stage B: development hard eval

- run on a small non-final dev seed set;
- if success is near zero and mean gates do not exceed PPO frontier behavior,
  do not generate PPO data yet. Tune MPPI cost/model/horizon first.

Stage C: validation hard eval

- run on `validation_unseen 101-200`;
- compare against current PPO best:
  `21%` success, `1.66` mean gates, `79%` crash.

Promotion:

- if MPPI reaches `>=60%` success and `<=7.0s` mean successful time, it is a
  viable controller candidate and a strong teacher;
- if MPPI reaches `>=40%` success or clearly expands the solved-seed set, use
  successful episodes as teacher data for PPO;
- if MPPI stays near PPO plateau, continue improving MPPI costs/dynamics before
  any PPO imitation work.

## Dataset Rule

Only generate PPO imitation data after a written MPPI analysis packet confirms
useful hard-eval evidence.

Dataset contents:

- observation at each control step;
- MPPI action `[roll, pitch, yaw, thrust]`;
- normalized action if using PPO action scaling;
- seed, target gate, gate progress, termination reason, success flag;
- optional MPPI diagnostics such as best cost, cost quantiles, and selected
  horizon action sequence.

Generated datasets are artifacts, not source. Keep them out of git unless the
user explicitly asks otherwise.

## Post-Run Rule

After each MPPI oracle evaluation:

- write an analysis packet under `experiments/level3_ppo_loop/analysis/`;
- summarize whether MPPI beats the PPO frontier;
- choose exactly one next action:
  `hold_for_more_analysis`, `continue_same_hypothesis`,
  `launch_named_structural_lane`, or `start_teacher_dataset_generation`;
- write a reader note in plain Chinese under `drone_notes/level3_loops/`;
- commit and push small source/state/analysis/decision/note changes only.
