# Decision: Launch v62c Tanh-Squashed Gaussian Baseline

Date: 2026-06-27

## Decision

```text
continue_same_hypothesis
```

Continue the Brax/JAX clean reference-command tracker lane, but make
`tanh_squashed_gaussian` the formal default action distribution for future
bounded training.

## Why

The user explicitly chose the formal long-training route. Compared with v62b's
clipped-Gaussian stopgap, v62c has a cleaner PPO contract:

```text
sample pre-tanh action
tanh to env action
store env action
compute logprob with tanh Jacobian correction
```

This avoids the long-term mismatch created by hard clipping sampled Gaussian
actions at the environment boundary.

## Evidence

Analysis packet:

```text
experiments/level3_ppo_loop/analysis/2026-06-27_v62c_tanh_squashed_gaussian_support.md
```

Support checks passed:

- smoke metadata recorded `action_distribution=tanh_squashed_gaussian`;
- smoke metadata recorded
  `action_logprob_mode=tanh_squashed_gaussian_logprob_with_jacobian`;
- smoke rollout action clipping was `0.0`;
- smoke logprob/env consistency error was about `3.18e-7`;
- audit verdicts had `action_clipping=ok` and
  `action_sampling_logprob=ok`;
- audit stored-vs-env logprob abs mean was about `3.21e-7`;
- tracker env unit tests passed: `33 passed`;
- `config/level3.toml` and `config/level3_tracker_free_space.toml` were not
  modified.

## Guardrails

- Do not add gate/aperture/race/finish/stage reward.
- Do not add gate/obstacle/planner-phase actor inputs to the clean tracker.
- Do not modify `config/level3.toml`.
- Do not resume v62b clipped-Gaussian checkpoints into v62c unless a future
  packet explicitly approves a cross-distribution experiment.
- Do not treat the 1024-step smoke as learning evidence.
- Monitor value/advantage scale during v62c training; the audit still marked
  advantage scale as `large`.

## Next Action

Run a bounded v62c online W&B chunk before any 60M+ maturation:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62c_tanh_squashed_gaussian_10m \
  --config level3_tracker_free_space.toml \
  --seed 26310 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 10027008 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 1048576 \
  --checkpoint-path lsy_drone_racing/control/checkpoints/v62c_tanh_squashed_gaussian_10m/v62c_tanh_squashed_gaussian_10m_final.pkl \
  --summary-json experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62c_tanh_squashed_gaussian_10m_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --wandb-enabled \
  --wandb-mode online \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-entity aojili77-technical-university-of-munich \
  --wandb-run-name v62c_tanh_squashed_gaussian_10m \
  --wandb-run-id v62c_tanh_squashed_gaussian_10m_20260627 \
  --jax-device gpu
```

After that run, evaluate saved milestones and compare against v62b's 10M
signal. Only then decide whether to extend, fix value/return scale, or tune the
command reward.
