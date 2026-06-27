# v62d_001 Hypothesis

Date: 2026-06-27

## Candidate

```text
id: v62d_001
family: A_value_return_stabilization
lane_name: v62d_001_value_target_scale50_30m
```

## Hypothesis

v62c learned spatial tracking but velocity obedience degraded early. The
milestone review found that:

```text
best overall v62c checkpoint: 7M
initial velocity error: 0.6465
1M velocity error: 0.8826
7M velocity error: 0.7397
8M velocity error: 0.8798
final velocity error: 0.8915
```

The likely failure mode is not action/logprob mismatch anymore. The
tanh-squashed action path is clean. The next smallest stabilization test is to
reduce critic target magnitude while keeping GAE and policy advantages in raw
reward units.

## Changed Knob

```text
--value-target-scale 50.0
```

The critic predicts `return / 50`, while GAE and advantages stay in raw reward
units. Reward semantics are unchanged.

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
  --lane-name v62d_001_value_target_scale50_30m \
  --config level3_tracker_free_space.toml \
  --seed 26411 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 8 \
  --update-epochs 4 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_001_value_target_scale50_30m/v62d_001_value_target_scale50_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_001_value_target_scale50_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --value-target-scale 50.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_001_value_target_scale50_30m \
  --wandb-run-id v62d_001_value_target_scale50_30m_20260627 \
  --jax-device gpu
```

`30015488` timesteps is intentional: with `1024 x 32 = 32768` samples/update,
this gives exactly `916` updates and avoids silently rounding below 30M.

## Evaluation Plan

Evaluate milestones and final:

```text
5M, 10M, 15M, 20M, 25M, 30M, final
```

Use the same held-out tracker protocol as v62c milestone review:

```text
seed=26310
num_envs=1024
num_steps=32
eval_rollouts=16
action_distribution=tanh_squashed_gaussian
```

Baseline is v62c 7M:

| Metric | v62c 7M |
|---|---:|
| reward | -4.8459 |
| position error | 0.6573 |
| cross-track error | 0.5214 |
| velocity error | 0.7397 |
| done mean | 0.00391 |
| balanced score | -7.5365 |

Promotion requires velocity error to improve by at least 10-15% without
position/cross-track/done/action-delta regression and with action/logprob audit
still clean.

