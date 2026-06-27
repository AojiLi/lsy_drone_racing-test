# v62d_004 Support Decision

Date: 2026-06-27

## Decision

Outcome:

```text
support_passed_ready_to_train
```

Launch `v62d_004_speed_bin_balanced_generator_30m` from scratch after committing
the support changes.

## Evidence

Support packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62d_004_speed_bin_balanced_generator_support.md
```

Hypothesis packet:

```text
experiments/level3_ppo_loop/v62d_candidates/v62d_004_hypothesis.md
```

Checker result:

```text
ALL GREEN
```

The support change adds a gated generator profile:

```text
--command-generator-profile speed_bin_balanced
```

Default generator behavior remains available as `default`. The training,
smoke, and audit paths propagate the selected profile, and checkpoint/summary
metadata record it.

## Boundaries

Preserved:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
actor observation remains level3_reference_tracker_command_v3
action_distribution remains tanh_squashed_gaussian
no gate/aperture/race/finish/stage reward
no gate/obstacle/planner-phase actor inputs
candidate trains from scratch
```

## Approved Command

```bash
mkdir -p lsy_drone_racing/control/checkpoints/v62d_004_speed_bin_balanced_generator_30m \
  experiments/level3_ppo_loop/analysis/tracker_stage_metrics && \
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_004_speed_bin_balanced_generator_30m \
  --config level3_tracker_free_space.toml \
  --seed 26441 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 30015488 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 5000000 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62d_004_speed_bin_balanced_generator_30m/v62d_004_speed_bin_balanced_generator_30m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62d_004_speed_bin_balanced_generator_30m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --value-target-scale 1.0 \
  --eval-rollouts 16 \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62d_004_speed_bin_balanced_generator_30m \
  --wandb-run-id v62d_004_speed_bin_balanced_generator_30m_20260627 \
  --jax-device gpu
```

## Post-Run Requirements

After training, evaluate:

```text
5M / 10M / 15M / 20M / 25M / 30M / final
```

Select the best milestone with the v62d multi-metric score, audit that best
checkpoint, run exactly three reviews, write analysis and decision packets,
write a Chinese reader note, update the registry and `state.json`, then commit
and push code/docs/state/analysis/decision/note changes.
