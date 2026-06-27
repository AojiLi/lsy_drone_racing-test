# v62d_002 Hypothesis

Date: 2026-06-27

## Candidate

```text
id: v62d_002
family: D_PPO_stabilizer
lane_name: v62d_002_value_scale50_conservative_ppo_30m
```

## Hypothesis

`v62d_001` proved that `value_target_scale=50.0` can stabilize the critic:

```text
final value_loss: 0.0006676
final explained_variance: 0.8662
best audit advantage_scale: ok
```

But the policy became an aggressive spatial chaser:

```text
best v62d_001 velocity error: 1.2018
v62c 7M velocity error: 0.7397
best v62d_001 done mean: 0.02903
v62c 7M done mean: 0.00391
```

There was a confounder:

```text
v62c update pressure: 4 minibatches, 1 update epoch
v62d_001 update pressure: 8 minibatches, 4 update epochs
```

This candidate isolates that confounder. It keeps `value_target_scale=50.0` but
restores conservative v62c-like PPO update pressure.

## Changed Knobs

Relative to `v62d_001`:

```text
--num-minibatches 4
--update-epochs 1
```

Kept from `v62d_001`:

```text
--value-target-scale 50.0
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
  --lane-name v62d_002_value_scale50_conservative_ppo_30m \
  --config level3_tracker_free_space.toml \
  --seed 26421 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_002_value_scale50_conservative_ppo_30m/v62d_002_value_scale50_conservative_ppo_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_002_value_scale50_conservative_ppo_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --value-target-scale 50.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_002_value_scale50_conservative_ppo_30m \
  --wandb-run-id v62d_002_value_scale50_conservative_ppo_30m_20260627 \
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

