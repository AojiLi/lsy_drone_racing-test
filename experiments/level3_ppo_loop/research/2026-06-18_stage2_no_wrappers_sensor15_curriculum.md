# Level3 PPO Stage 2 Experiment: No-Wrappers + Sensor15 Curriculum

## Decision

Run one bounded Stage 2 structural train/evaluate chunk after explicit user
approval to enter structural Stage 2.

This is not a reward-only move. It is a named structural curriculum probe. It
must be kept separate from reward-only trial records.

## Hypothesis

The only Stage 2 branch with non-zero hard-evaluator success was
`level3_loop_010_stage2_no_train_wrappers`, trained with
`config/level3_dr_stage2_no_train_wrappers.toml` and hard-evaluated on
`config/level3_dr.toml`.

The remaining bottleneck appears to be first-gate acquisition under hard
randomized geometry:

```text
level3_dr.toml gate0_inside_sensor_range_xy_rate = 0.17
obstacle0_corridor_lt_0p2_rate = 0.348
obstacle0_corridor_lt_0p4_rate = 0.672
```

The new probe keeps the accepted no-train-wrapper branch and adds exactly one
curriculum change: raise the training sensor range from `0.7` to `1.5`.

## Training Config

Train with:

```text
config/level3_dr_stage2_no_wrappers_sensor15.toml
```

Hard evaluate with:

```text
config/level3_dr.toml
```

## What Changes

Compared with the current target config:

- remove train-only robustness wrappers, as in the accepted loop010 branch;
- raise training `env.sensor_range` from `0.7` to `1.5`.

Compared with the loop010 accepted training branch:

- only raise training `env.sensor_range` from `0.7` to `1.5`.

Keep unchanged:

- hard eval config: `level3_dr.toml`;
- PPO hyperparameters;
- algorithm;
- network;
- observation layout: `obstacle_heading_xy_v1`;
- reward channel set;
- active reward numbers from loop010;
- full Level3 track randomization;
- env action and dynamics disturbances;
- gate, obstacle, drone, mass, and inertia randomizations.

## Geometry Check

Diagnostic command:

```bash
pixi run -e gpu python scripts/sample_level3_first_gate_geometry.py \
  --config level3_dr_stage2_no_wrappers_sensor15.toml \
  --seed-start 1 \
  --num-seeds 500 \
  --out-prefix experiments/level3_ppo_loop/diagnostics/level3_stage2_no_wrappers_sensor15_geometry_500
```

Result:

```text
gate0_visible_rate = 0.622
gate0_inside_sensor_range_xy_rate = 0.622
obstacle0_corridor_lt_0p2_rate = 0.348
obstacle0_corridor_lt_0p4_rate = 0.672
gate0_horizontal_distance_median = 1.287
gate0_horizontal_distance_p95 = 2.107
```

Interpretation:

- the curriculum increases first-gate observability;
- it does not make obstacle0/corridor geometry easier;
- hard evaluation remains unchanged, so acceptance still depends on transfer
  back to `level3_dr.toml`.

## Starting Checkpoint

Continue from the current hard-evaluator incumbent:

```text
lsy_drone_racing/control/checkpoints/level3_loop_010_stage2_no_train_wrappers/level3_loop_010_stage2_no_train_wrappers_step_015000000.ckpt
```

Current incumbent metrics:

```text
success_rate = 0.05
mean_time_s_success = 5.64
mean_gates = 0.80
crash_rate = 0.95
```

## Reward Numbers

Use the loop010 reward numbers exactly. Do not use loop014 numbers and do not
let the automatic reward proposer alter this structural test.

```text
gate_stage_coef=14
gate_axis_coef=28
gate_bonus=220
gate_front_bonus=10
gate_back_bonus=45
finish_bonus=190
wrong_side_penalty=8
crash_penalty=55
obstacle_coef=5.25
obstacle_margin=0.2
timeout_penalty=80
time_penalty=0.015
act_coef=0.015
d_act_th_coef=0.075
d_act_xy_coef=0.08
cmd_tilt_coef=0.9
rpy_coef=0.75
tilt_limit_deg=38
tilt_excess_coef=14
```

Disabled reward channels must remain disabled:

```text
progress_coef=0
near_gate_coef=0
gate_plane_bonus=0
missed_gate_penalty=0
obstacle_clearance_coef=0
```

## Run Shape

Run exactly one chunk:

```text
train_timesteps = 30000000
checkpoint_interval = 5000000
max_eval_checkpoints = 6
```

Use W&B project:

```text
ADR-PPO-Racing-Level3
```

After the run, immediately execute:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

## Acceptance Gate

Accept this branch only if hard eval on `level3_dr.toml` improves over loop010:

- `success_rate > 0.05`, or
- `crash_rate < 0.95` with `mean_gates >= 0.80`, or
- W&B `passed_gate_rate` / `finished_rate` conversion improves and is confirmed
  by evaluator metrics.

If any checkpoint has non-zero success, run a 100-seed hard re-eval before
treating it as robust progress.

Reject or hold if:

- `success_rate == 0.0`;
- `mean_gates < 0.80`;
- hard-eval crashes remain concentrated at gates 0/1 without conversion;
- W&B reward improves without evaluator gate/finish progress.

## Approved Dry-Run Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --max-eval-checkpoints 6 \
  --config level3_dr_stage2_no_wrappers_sensor15.toml \
  --eval-config level3_dr.toml \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --override-state-hold \
  --proposal-name stage2_no_wrappers_sensor15_curriculum \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_010_stage2_no_train_wrappers/level3_loop_010_stage2_no_train_wrappers_step_015000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_010_stage2_no_train_wrappers_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/research/2026-06-18_stage2_no_wrappers_sensor15_curriculum.md \
  --param gate_stage_coef=14 \
  --param gate_axis_coef=28 \
  --param gate_bonus=220 \
  --param gate_front_bonus=10 \
  --param gate_back_bonus=45 \
  --param finish_bonus=190 \
  --param wrong_side_penalty=8 \
  --param crash_penalty=55 \
  --param obstacle_coef=5.25 \
  --param obstacle_margin=0.2 \
  --param timeout_penalty=80 \
  --param time_penalty=0.015 \
  --param act_coef=0.015 \
  --param d_act_th_coef=0.075 \
  --param d_act_xy_coef=0.08 \
  --param cmd_tilt_coef=0.9 \
  --param rpy_coef=0.75 \
  --param tilt_limit_deg=38 \
  --param tilt_excess_coef=14
```

Do not use `--max-iterations > 1`. Do not continue automatically after this
chunk without the required post-run analysis.
