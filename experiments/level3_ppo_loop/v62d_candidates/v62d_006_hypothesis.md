# v62d_006 Hypothesis

Date: 2026-06-27

## Candidate

```text
v62d_006_speedbin_longrollout_256x128
```

Family:

```text
D_PPO_stabilizer
```

## Hypothesis

`v62d_004` showed that the `speed_bin_balanced` generator is useful, especially
for position and cross-track tracking under planner-like command sequences.
`v62d_005` showed that value target scaling can make critic diagnostics look
healthier, but it does not solve velocity obedience and can push the policy
toward large, rough actions.

The next clean single knob is rollout horizon:

```text
1024 envs x 32 steps -> 256 envs x 128 steps
```

The batch size remains `32768` samples/update, but the temporal window expands
from `0.64s` to `2.56s` at 50 Hz. This may better cover:

```text
approach deceleration
hold/brake settling
low-speed-through continuation
recover-speed transitions
```

Do not change reward semantics, observation layout, action distribution, or
track config.

## Changed Knobs

```text
command_generator_profile=speed_bin_balanced
num_envs=256
num_steps=128
value_target_scale=1.0
command_vel_error_coef=default
num_minibatches=4
update_epochs=1
```

No observation-layout change. No gate, aperture, race, finish, or stage reward.
Train from scratch after support passes.

## Support Gate

Builder/checker support is required before the 30M candidate because rollout
geometry changes training semantics.

Support smoke command:

```bash
mkdir -p lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_support \
  experiments/level3_ppo_loop/analysis/tracker_stage_metrics && \
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_006_speedbin_longrollout_256x128_support \
  --config level3_tracker_free_space.toml \
  --seed 26460 \
  --num-envs 256 \
  --num-steps 128 \
  --total-timesteps 262144 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 131072 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_support/v62d_006_speedbin_longrollout_256x128_support_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_006_speedbin_longrollout_256x128_support_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --value-target-scale 1.0 \
  --eval-rollouts 4 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_006_speedbin_longrollout_256x128_support \
  --wandb-run-id v62d_006_speedbin_longrollout_256x128_support_20260627 \
  --jax-device gpu
```

Support checker should verify:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
checkpoint metadata num_envs=256 and num_steps=128
observation_layout=level3_reference_tracker_command_v3
action_distribution=tanh_squashed_gaussian
command_generator_profile=speed_bin_balanced
reward_coefficients={}
finite metrics and checkpoint reload
action/logprob support audit clean enough to launch 30M
```

## Training Command After Support Passes

```bash
mkdir -p lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_30m \
  experiments/level3_ppo_loop/analysis/tracker_stage_metrics && \
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_006_speedbin_longrollout_256x128_30m \
  --config level3_tracker_free_space.toml \
  --seed 26461 \
  --num-envs 256 \
  --num-steps 128 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_006_speedbin_longrollout_256x128_30m/v62d_006_speedbin_longrollout_256x128_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_006_speedbin_longrollout_256x128_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_006_speedbin_longrollout_256x128_30m \
  --wandb-run-id v62d_006_speedbin_longrollout_256x128_30m_20260627 \
  --jax-device gpu
```

## Acceptance

Evaluate `5M / 10M / 15M / 20M / 25M / 30M / final`, audit the best milestone,
and compare against:

```text
standing frontier: v62c 7M default baseline
same-distribution baseline: v62c 7M under speed_bin_balanced
previous speed-bin best: v62d_004 5M
v62d_005 15M diagnostic best
```

Promotion still requires materially improved velocity obedience without
unacceptable position/cross-track, done-rate, action-smoothness, or action-path
regression.

