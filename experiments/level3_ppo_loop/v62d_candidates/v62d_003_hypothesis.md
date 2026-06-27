# v62d_003 Hypothesis

Date: 2026-06-27

## Candidate

```text
id: v62d_003
family: B_velocity_obedience_reward_numbers
lane_name: v62d_003_velocity_coef_2x_30m
```

## Hypothesis

v62c, v62d_001, and v62d_002 all show the same pressure:

```text
spatial tracking improves
velocity obedience worsens
done/action_delta drift upward
```

v62d_002 closes the narrow value-scale isolation question. Conservative PPO
settings made the value-scale run less extreme than v62d_001, but it still did
not beat the v62c 7M frontier.

This candidate tests one generic tracker reward-number change:

```text
ReferenceCommandReward vel_error_coef: 0.6 -> 1.2
```

The goal is to make the policy pay more attention to the desired trajectory
velocity instead of winning position/cross-track by aggressive reference
chasing.

## Changed Knobs

Relative to v62c-style v62 baseline:

```text
--command-vel-error-coef 1.2
```

Kept:

```text
--value-target-scale 1.0
--num-minibatches 4
--update-epochs 1
--action-distribution tanh_squashed_gaussian
--num-envs 1024
--num-steps 32
```

## Fixed Boundaries

- Train from scratch.
- Keep actor observation `level3_reference_tracker_command_v3`.
- Keep `action_distribution=tanh_squashed_gaussian`.
- Do not add gate, obstacle, planner-phase, aperture, race, finish, or stage
  actor inputs.
- Do not add gate/aperture/race/finish/stage reward.
- Do not modify `config/level3.toml`.
- Do not modify `config/level3_tracker_free_space.toml`.

## Training Command

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

`30015488` timesteps equals `916` updates at `1024 x 32`, so the run does not
round below 30M.

## Evaluation Plan

Evaluate:

```text
5M, 10M, 15M, 20M, 25M, 30M, final
```

Use the same held-out tracker protocol:

```text
seed=26310
num_envs=1024
num_steps=32
eval_rollouts=16
action_distribution=tanh_squashed_gaussian
```

Promotion still requires beating v62c 7M primarily on velocity while not
regressing position, cross-track, done, action delta, or audit health.
