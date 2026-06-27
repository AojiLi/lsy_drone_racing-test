# v62d_007 Hypothesis

Date: 2026-06-27

## Candidate

```text
v62d_007_speedbin_velocity_coef_2x
```

Family:

```text
E_best_of_family_combination
```

## Hypothesis

`v62d_004` showed that `speed_bin_balanced` gives the strongest spatial tracking
signal so far under planner-like command distributions. `v62d_003` showed that
a stronger generic velocity-error coefficient gives the only direct velocity
improvement signal, but it was too weak alone. `v62d_006` showed that increasing
rollout horizon to `256x128` does not solve velocity obedience and slows the
loop.

The next test should combine the two partial single-family signals:

```text
speed_bin_balanced generator
+ generic command velocity coefficient 1.2
```

Return to the faster and previously cleaner rollout geometry:

```text
1024 envs x 32 steps
```

Do not change observation layout, action distribution, track config, gate
rewards, aperture rewards, race rewards, finish rewards, stage rewards, or
planner-phase inputs.

## Changed Knobs

```text
command_generator_profile=speed_bin_balanced
command_vel_error_coef=1.2
num_envs=1024
num_steps=32
value_target_scale=1.0
num_minibatches=4
update_epochs=1
action_distribution=tanh_squashed_gaussian
```

## Support Gate

Run a small support smoke/checker before 30M training because this combines a
generator-distribution knob with a reward-number knob.

Support smoke command:

```bash
mkdir -p lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_support \
  experiments/level3_ppo_loop/analysis/tracker_stage_metrics && \
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_007_speedbin_velocity_coef_2x_support \
  --config level3_tracker_free_space.toml \
  --seed 26470 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 262144 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 131072 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_support/v62d_007_speedbin_velocity_coef_2x_support_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_support_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --command-vel-error-coef 1.2 \
  --value-target-scale 1.0 \
  --eval-rollouts 4 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_007_speedbin_velocity_coef_2x_support \
  --wandb-run-id v62d_007_speedbin_velocity_coef_2x_support_20260627 \
  --jax-device gpu
```

Support checker must verify:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
observation_layout=level3_reference_tracker_command_v3
action_distribution=tanh_squashed_gaussian
command_generator_profile=speed_bin_balanced
reward_coefficients only override generic command vel_error_coef=1.2
no gate/aperture/obstacle/race/finish/stage rewards
checkpoint metadata records the combined knobs
action/logprob support audit is clean enough to launch 30M
```

## Training Command After Support Passes

```bash
mkdir -p lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_30m \
  experiments/level3_ppo_loop/analysis/tracker_stage_metrics && \
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_007_speedbin_velocity_coef_2x_30m \
  --config level3_tracker_free_space.toml \
  --seed 26471 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_30m/v62d_007_speedbin_velocity_coef_2x_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --command-vel-error-coef 1.2 \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_007_speedbin_velocity_coef_2x_30m \
  --wandb-run-id v62d_007_speedbin_velocity_coef_2x_30m_20260627 \
  --jax-device gpu
```

## Acceptance

Evaluate `5M / 10M / 15M / 20M / 25M / 30M / final`, audit the best milestone,
and compare against:

```text
standing frontier: v62c 7M default baseline
same-distribution baseline: v62c 7M under speed_bin_balanced
previous speed-bin best: v62d_004 5M
previous long-rollout best: v62d_006 20M
```

Promotion requires materially improved velocity obedience without unacceptable
position/cross-track, done-rate, action-smoothness, or action-path regression.
