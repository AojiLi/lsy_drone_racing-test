# v62d_007 Support Decision

Date: 2026-06-27

## Decision

Outcome:

```text
continue_same_hypothesis
```

Support passes for:

```text
v62d_007_speedbin_velocity_coef_2x_30m
```

Launch the 30M candidate from scratch.

## Evidence

Support packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_007_speedbin_velocity_coef_2x_support.md
```

Hypothesis packet:

```text
experiments/level3_ppo_loop/v62d_candidates/v62d_007_hypothesis.md
```

Support artifacts:

```text
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_support_summary.json
experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_007_speedbin_velocity_coef_2x_support_audit.json
```

Support checkpoint:

```text
lsy_drone_racing/control/checkpoints/v62d_007_speedbin_velocity_coef_2x_support/v62d_007_speedbin_velocity_coef_2x_support_final.pkl
```

Checker:

```text
ALL GREEN
```

Key support evidence:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
observation_layout=level3_reference_tracker_command_v3
action_distribution=tanh_squashed_gaussian
command_generator_profile=speed_bin_balanced
reward_coefficients={"vel_error_coef": 1.2}
summary and audit finite
action_clipping=ok
action_sampling_logprob=ok
stored_vs_env_logprob_abs_mean=3.12e-7
```

The support audit reports:

```text
advantage_scale=large
```

This is monitor-only for support. It must be inspected after the 30M run but
does not block launching the bounded candidate.

## Launch Command

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

After the run, evaluate `5M / 10M / 15M / 20M / 25M / 30M / final`, audit the
best checkpoint, and run the three required reviewers before any next
candidate.
