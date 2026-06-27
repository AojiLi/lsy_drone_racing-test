# v62d_003 Velocity Coefficient 2x Support

Date: 2026-06-27

## Purpose

Prepare the next high-budget generic reference-tracker candidate:

```text
v62d_003_velocity_coef_2x
```

This is support for a training candidate, not a completed candidate analysis.

## Candidate Rationale

v62d_001 and v62d_002 both improved spatial tracking but failed the frontier on
velocity obedience, done rate, and action smoothness.

The v62d_002 decision closed the value-scale isolation question:

```text
value_target_scale=50.0 fixed critic scale
conservative PPO reduced severity
but v62d_002 still did not beat v62c 7M
```

The next single-family test is Family B:

```text
B_velocity_obedience_reward_numbers
```

Single reward knob:

```text
ReferenceCommandReward vel_error_coef: 0.6 -> 1.2
```

This remains generic command-tracker training. It does not add gate,
aperture, obstacle, planner-phase, race, finish, or stage inputs/rewards.

## Implementation

Changed files:

```text
scripts/benchmark_v60_brax_rollout.py
scripts/train_v60_brax_ppo_smoke.py
scripts/train_v62_brax_reference_command_tracker.py
```

Support added:

```text
--command-vel-error-coef <float>
```

The override is explicit and optional. When omitted, defaults remain unchanged.
When provided, it creates:

```text
reward_coefficients = {"vel_error_coef": <value>}
```

and passes it into the JAX `command_reward` path.

The checkpoint and summary metadata record:

```text
reward_coefficients
```

so v62d_003 can be reproduced from the training command and checkpoint metadata.

## Builder Checks

Syntax:

```bash
pixi run -e gpu python -m py_compile \
  scripts/benchmark_v60_brax_rollout.py \
  scripts/train_v60_brax_ppo_smoke.py \
  scripts/train_v62_brax_reference_command_tracker.py
```

Result: passed.

Tiny support smoke:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_003_velocity_coef_2x_support_smoke \
  --config level3_tracker_free_space.toml \
  --seed 26431 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 32768 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 32768 \
  --checkpoint-path /tmp/v62d_003_velocity_coef_2x_support_smoke.pkl \
  --summary-json /tmp/v62d_003_velocity_coef_2x_support_smoke.json \
  --action-distribution tanh_squashed_gaussian \
  --command-vel-error-coef 1.2 \
  --value-target-scale 1.0 \
  --eval-rollouts 1 \
  --jax-device gpu
```

Result:

```text
global_step: 32768
reward_coefficients: {"vel_error_coef": 1.2}
all_finite: 1.0
rollout_action_logprob_env_consistency_error: 3.17e-7
eval has learning signal: true
```

## Checker Result

Read-only checker result:

```text
ALL GREEN
```

Checker verified:

- diff is limited to the intended scripts;
- omitted `--command-vel-error-coef` keeps default reward behavior equivalent;
- explicit `1.2` only overrides clean command reward `vel_error_coef`;
- the override is recorded in checkpoint and summary metadata;
- `observation_layout` remains `level3_reference_tracker_command_v3`;
- reward scope remains `no gate/aperture/obstacle/race/finish/stage reward`;
- `action_distribution` remains `tanh_squashed_gaussian`;
- `config/level3.toml` and `config/level3_tracker_free_space.toml` are
  unchanged;
- py_compile, diff-check, and a 32,768-step checker smoke passed.

## Approved Training Command

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_003_velocity_coef_2x_30m \
  --config level3_tracker_free_space.toml \
  --seed 26431 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_003_velocity_coef_2x_30m/v62d_003_velocity_coef_2x_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_003_velocity_coef_2x_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-vel-error-coef 1.2 \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_003_velocity_coef_2x_30m \
  --wandb-run-id v62d_003_velocity_coef_2x_30m_20260627 \
  --jax-device gpu
```

This command trains from scratch and satisfies the high-budget candidate
minimum of 30M timesteps.
