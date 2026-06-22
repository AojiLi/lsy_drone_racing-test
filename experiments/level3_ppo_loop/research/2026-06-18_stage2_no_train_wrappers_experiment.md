# Level3 PPO Stage 2 Experiment: No Train-Only Robustness Wrappers

## Decision

Run one bounded Stage 2 train/eval chunk to isolate whether train-only
robustness wrappers are blocking Level3 gate acquisition before the policy has
stable competence.

This is not a reward-only move. Reward-only tuning has already met the
exhaustion gate and Stage 2 structural diagnostics are open.

## Local Evidence

- Current refreshed best:
  `level3_loop_004_gate_acquisition_safety:30M`
- Current refreshed best hard eval:
  - `success_rate = 0.0`
  - `crash_rate = 1.0`
  - `mean_gates = 0.9`
  - `mean_time_s_success = null`
- Reward-only search did not produce any successful episodes.
- Observation/event parity bug was fixed and verified clean.
- Action scaling parity was verified clean.
- Gate-box reward geometry experiment failed and has been rolled back.

## Hypothesis

The current `level3_dr.toml` training distribution stacks full Level3 track
randomization with extra train-only robustness wrappers:

- thrust scale and battery sag
- command latency
- command response lag
- observation latency
- observation noise

Hard eval on `level3_dr.toml` does not apply these train-only wrappers. The
policy may be learning under a harder distribution before it can reliably pass
the first gates.

## Experiment

Train with:

- `config/level3_dr_stage2_no_train_wrappers.toml`

Evaluate with:

- `config/level3_dr.toml`
- `ppo_level3_inference`

Keep unchanged:

- PPO hyperparameters
- observation layout
- network architecture
- reward channel set
- active reward numbers from the current global best branch
- full Level3 track randomization
- env action and dynamics disturbances
- gate and obstacle randomizations
- hard eval config

Change only:

- remove `[train.*]` train-only wrappers for this diagnostic branch.

## Reward Numbers

Use the current global-best branch values:

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

Disabled channels stay disabled:

```text
progress_coef=0
near_gate_coef=0
gate_plane_bonus=0
missed_gate_penalty=0
obstacle_clearance_coef=0
```

## Acceptance Gate

Accept the branch only if hard eval on `level3_dr.toml` shows at least one:

- `success_rate > 0.0`
- `crash_rate < 1.0`
- `mean_gates > 0.9`
- clear W&B conversion in `race/passed_gate_rate` or `race/finished_rate` that
  matches evaluator progress

Reject and hold if:

- best checkpoint remains `success_rate = 0.0`, `crash_rate = 1.0`, and
  `mean_gates <= 0.9`
- W&B reward improves without hard-eval progress
- PPO instability appears without evaluator conversion

## Command Shape

Use one 30M chunk, checkpoint every 5M, then run the required post-run W&B
analysis before any next train/eval chunk.

The command must attach this packet as `--approved-hypothesis-packet` and keep
hard eval on `level3_dr.toml`.
