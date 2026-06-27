# v62d_005 Hypothesis

Date: 2026-06-27

## Candidate

```text
v62d_005_speedbin_value_scale10
```

Family:

```text
A_value_return_stabilization
```

## Hypothesis

`v62d_004` showed that the `speed_bin_balanced` generator improves position and
cross-track tracking under a speed-bin distribution, but it peaks early and
drifts after `5M`. The final training batch still shows weak critic/value
health:

```text
explained_variance ~= 0
values_std ~= 0.0015
value_loss remains high
returns are large negative
```

`v62d_001` and `v62d_002` already showed `value_target_scale=50.0` is too
aggressive or not sufficient under the default generator. This candidate tests
a narrower critic target scale while keeping the more useful speed-bin command
distribution.

## Changed Knobs

```text
command_generator_profile=speed_bin_balanced
value_target_scale=10.0
command_vel_error_coef=default
num_minibatches=4
update_epochs=1
```

No observation-layout change. No reward-semantics change. No gate, aperture,
race, finish, or stage reward. Train from scratch.

## Training Command

```bash
mkdir -p lsy_drone_racing/control/checkpoints/v62d_005_speedbin_value_scale10_30m \
  experiments/level3_ppo_loop/analysis/tracker_stage_metrics && \
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_005_speedbin_value_scale10_30m \
  --config level3_tracker_free_space.toml \
  --seed 26451 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_005_speedbin_value_scale10_30m/v62d_005_speedbin_value_scale10_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_005_speedbin_value_scale10_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --value-target-scale 10.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_005_speedbin_value_scale10_30m \
  --wandb-run-id v62d_005_speedbin_value_scale10_30m_20260627 \
  --jax-device gpu
```

## Acceptance

Evaluate `5M / 10M / 15M / 20M / 25M / 30M / final`, audit the best milestone,
and compare against:

```text
standing frontier: v62c 7M default baseline
same-distribution baseline: v62c 7M under speed_bin_balanced
v62d_004 5M best
```

Promotion still requires materially improved velocity obedience without
unacceptable position/cross-track, done-rate, or action-smoothness regression.
