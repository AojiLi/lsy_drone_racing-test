# v60 Command-Trajectory Reward Bounded Smoke

Date: 2026-06-26

## Run

Task: `reference_command_no_gate_reward`

Purpose: rerun the bounded v60 smoke after replacing pure current-point reward
with command-aware trajectory reward. This is a plumbing and semantics check,
not a learning judgment.

Command:

```bash
pixi run -e gpu python lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  --config level3_tracker_free_space.toml \
  --task reference_command_no_gate_reward \
  --tracker-env-mode free_space \
  --observation-layout auto \
  --seed 26065 \
  --total-timesteps 4096 \
  --num-envs 16 \
  --num-steps 256 \
  --num-minibatches 4 \
  --update-epochs 4 \
  --checkpoint-interval 0 \
  --model-path lsy_drone_racing/control/checkpoints/v60_reference_command_trajectory_reward_smoke/v60_reference_command_trajectory_reward_smoke_final.ckpt \
  --wandb-enabled \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v60_reference_command_trajectory_reward_smoke_4096 \
  --wandb-run-id v60_reference_command_trajectory_reward_smoke_20260626 \
  --wandb-mode online \
  --jax-device gpu \
  --cuda
```

W&B: <https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/v60_reference_command_trajectory_reward_smoke_20260626>

Checkpoint:

```text
lsy_drone_racing/control/checkpoints/v60_reference_command_trajectory_reward_smoke/v60_reference_command_trajectory_reward_smoke_final.ckpt
```

## Checkpoint Metadata

- task: `reference_command_no_gate_reward`
- observation layout: `level3_reference_tracker_command_v3`
- obs dim: `56`
- reward model: `reference_command_reward`
- global step: `4096`
- total timesteps: `4096`
- num envs: `16`
- num steps: `256`

Reward coefficients:

- `gate_center_coef = 0.0`
- `obstacle_coef = 0.0`
- `gate_x_progress_coef = 0.0`
- `gate_cross_bonus = 0.0`
- `gate_recover_bonus = 0.0`
- `gate_linger_penalty_coef = 0.0`
- `trajectory_cross_track_coef = 1.2`
- `trajectory_along_speed_coef = 0.7`
- `trajectory_reverse_speed_coef = 0.5`
- `trajectory_overshoot_coef = 1.4`
- `semantic_brake_speed_coef = 1.0`
- `semantic_slow_speed_coef = 0.8`
- `semantic_slow_stop_coef = 0.8`
- `semantic_recover_speed_coef = 0.4`

## Evaluation

Metrics command:

```bash
pixi run -e gpu python scripts/evaluate_level3_tracker_stage.py \
  --stage reference_command_no_gate_reward \
  --checkpoint lsy_drone_racing/control/checkpoints/v60_reference_command_trajectory_reward_smoke/v60_reference_command_trajectory_reward_smoke_final.ckpt \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v60_reference_command_trajectory_reward_smoke_metrics.json \
  --episodes 20 \
  --seeds 101-120 \
  --max-episode-steps 500
```

Gate command:

```bash
pixi run -e tests python scripts/check_level3_tracker_stage_gate.py \
  --stage reference_command_no_gate_reward \
  --metrics-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v60_reference_command_trajectory_reward_smoke_metrics.json \
  --output experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v60_reference_command_trajectory_reward_smoke_gate.json
```

Gate checker exited with code `2`, as expected for a 4096-step smoke that has
not learned the stage yet.

## Results

Plumbing/semantic checks:

- checkpoint backed: `true`
- all finite: `true`
- semantic waypoint type count: `4.0`
- W&B logged the new `tracker/command_*` and `tracker/trajectory_*` diagnostics
- `config/level3.toml` diff: empty

Learning gate metrics:

- success rate: `0.0`
- crash rate: `1.0`
- mean brake/hold position error: `0.6842m`
- mean slow-through position error: `0.6464m`
- mean brake/hold speed: `0.1803m/s`
- p90 brake/hold speed: `0.2915m/s`
- mean slow-through speed: `0.4001m/s`
- brake-hold rush count: `0`
- slow-through stop count: `0`
- mean action delta L2: `0.00049`
- mean action norm L2: `0.03695`

Stage gate:

- passed: `false`
- next stage unlocked: `null`

Failed learning metrics:

- `success_rate >= 0.8`
- `crash_rate <= 0.08`
- `mean_brake_hold_position_error_m <= 0.2`
- `mean_slow_through_position_error_m <= 0.24`
- `mean_brake_hold_speed_mps <= 0.16`
- `p90_brake_hold_speed_mps <= 0.28`

Passed metrics:

- checkpoint backed
- all finite
- waypoint type count
- slow-through speed lower and upper bounds
- brake-hold rush count
- slow-through stop count

## Interpretation

This smoke is clean. It proves that the v60 command-trajectory reward can train
for one bounded preflight update, save a checkpoint, sync W&B, evaluate the
stage, and produce machine-checkable gate results.

The gate failure is not evidence against the reward or architecture. Per the
tracker-loop long-stage policy, a `4096`-step smoke can reject broken plumbing
but cannot reject PPO learning. The stage budget for real maturation is `8M`
timesteps, with a possible `20M` research extension.

## Next Action

Continue the same v60 hypothesis with an explicit bounded maturation run:

```text
reference_command_no_gate_reward, 8M timesteps, 1024 envs x 32 steps,
checkpoint interval 1M, W&B enabled, evaluate milestone checkpoints.
```

Do not promote to `planner_integration_smoke` yet.
