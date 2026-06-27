# v62d_006 Support Decision

Date: 2026-06-27

## Decision

Outcome:

```text
run_bounded_confirmation
```

Support passed for:

```text
v62d_006_speedbin_longrollout_256x128_30m
```

Approve one full 30M candidate run from scratch.

## Evidence

Support packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_006_longrollout_support.md
```

Hypothesis packet:

```text
experiments/level3_ppo_loop/v62d_candidates/v62d_006_hypothesis.md
```

Read-only checker result:

```text
ALL GREEN
```

Support checkpoint metadata verified:

```text
num_envs=256
num_steps=128
observation_layout=level3_reference_tracker_command_v3
action_distribution=tanh_squashed_gaussian
command_generator_profile=speed_bin_balanced
reward_coefficients={}
value_target_scale=1.0
```

Support action/logprob audit verified:

```text
action_clipping=ok
action_sampling_logprob=ok
stored_vs_env_logprob_abs_mean ~= 3.17e-7
sample_clip_fraction=0.0
```

Both config files remained unchanged:

```text
config/level3.toml
config/level3_tracker_free_space.toml
```

## Caveat

The long horizon makes raw return, reward, and advantage scale larger:

```text
advantage_scale=large
reward_scale=large
```

This is not a support blocker because the action path and finite checks passed,
but it must be monitored during the 30M run.

## Approved 30M Command

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

## Post-Run Requirements

After training:

```text
evaluate 5M / 10M / 15M / 20M / 25M / 30M / final
audit best checkpoint
spawn exactly three reviewers
write analysis packet
write decision packet
write Chinese reader note
update state and v62d registry
commit and push intended small files
```

