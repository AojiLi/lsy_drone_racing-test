# v62c Tanh-Squashed Gaussian PPO Support

Date: 2026-06-27

## Purpose

The user chose the long-training formalization route:

```text
raw_action ~ Normal(mean, std)
env_action = tanh(raw_action)
logprob includes the tanh Jacobian correction
```

This replaces v62b's temporary clipped-Gaussian action accounting as the default
future v62 lane. The goal of this packet is support validation only, not tracker
skill completion.

## Code Changes

- `scripts/train_v60_brax_ppo_smoke.py`
  - adds `--action-distribution`;
  - default is `tanh_squashed_gaussian`;
  - keeps `clipped_gaussian` as an explicit compatibility fallback;
  - separates raw actor mean from bounded deterministic env action;
  - computes tanh-squashed Gaussian logprob with a stable log-det-Jacobian term;
  - stores the env-executed bounded action in the PPO batch;
  - recomputes PPO update logprob with the selected action distribution.
- `scripts/train_v62_brax_reference_command_tracker.py`
  - exposes the same action-distribution choice;
  - records `action_distribution` and `action_logprob_mode` in checkpoint
    metadata and summary output.
- `scripts/audit_v62b_brax_ppo_signals.py`
  - can audit either action distribution;
  - for tanh mode, verifies stored logprob against the tanh-bounded env action.

The clean v60/v62 tracker contract is unchanged:

```text
observation_layout = level3_reference_tracker_command_v3
reward = reference_command_no_gate_reward
no gate/aperture/obstacle/race/finish/stage reward
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
```

## Package Note

The current GPU environment does not have `distrax` or
`tensorflow_probability.substrates.jax` installed. The implementation uses the
standard stable tanh log-det formula directly:

```text
log |det d tanh(x) / dx| = 2 * (log(2) - x - softplus(-2x))
```

Because this touches the PPO training semantics, the smoke/audit checks below
are the acceptance evidence. Adding a new distribution package remains optional
future cleanup, but should not block this lane.

## Smoke

Command:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62c_tanh_squashed_gaussian_smoke \
  --config level3_tracker_free_space.toml \
  --seed 26301 \
  --num-envs 16 \
  --num-steps 32 \
  --total-timesteps 1024 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 512 \
  --checkpoint-path /tmp/v62c_tanh_smoke.pkl \
  --summary-json /tmp/v62c_tanh_smoke_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --jax-device gpu
```

Key result:

| Metric | Value |
|---|---:|
| action distribution | `tanh_squashed_gaussian` |
| logprob mode | `tanh_squashed_gaussian_logprob_with_jacobian` |
| actual timesteps | `1024` |
| rollout action clip fraction | `0.0` |
| any-action clipped fraction | `0.0` |
| logprob/env consistency error | `3.18e-7` |
| all finite | `1.0` |
| has eval learning signal | `true` |

The tiny smoke is not learning evidence. It only proves the tanh action path
runs, saves metadata, and keeps the PPO action/logprob account consistent.

## Signal Audit

Command:

```bash
pixi run -e gpu python scripts/audit_v62b_brax_ppo_signals.py \
  --config level3_tracker_free_space.toml \
  --seed 26302 \
  --num-envs 256 \
  --num-steps 32 \
  --initial-log-std-values=-2.0 \
  --skip-checkpoint \
  --action-distribution tanh_squashed_gaussian \
  --output /tmp/v62c_tanh_audit.json \
  --jax-device gpu
```

Key audit result:

| Check | Result |
|---|---|
| action clipping | `ok` |
| action sampling/logprob | `ok` |
| initial std | `ok` |
| reward scale | `ok` |
| advantage scale | `large` |

Key values:

| Metric | Value |
|---|---:|
| std | `0.135335` |
| any-dim clipped fraction | `0.0` |
| sample clip fraction | `0.0` |
| stored-vs-env logprob abs mean | `3.21e-7` |
| stored-vs-env logprob abs p95 | `9.54e-7` |
| reward mean/std | `-2.4471 / 0.6373` |
| advantage mean/std | `-25.9112 / 9.2543` |

The remaining warning is not action-distribution correctness. It is the already
known value/advantage scale issue that should be monitored during bounded v62c
training.

## Checks

```text
py_compile: passed
ruff check: passed
ruff format --check: passed
pytest tests/unit/control/test_level3_reference_tracker_env.py -q: 33 passed
git diff --check: passed
config/level3.toml diff: empty
config/level3_tracker_free_space.toml diff: empty
```

## Interpretation

v62c is the formal action-distribution lane for future long training:

```text
v62b = quick validation/stopgap, clipped Gaussian with low std
v62c = long-training baseline, tanh-squashed Gaussian with Jacobian correction
```

Do not resume old v62b checkpoints into v62c unless a future packet explicitly
treats that as a cross-distribution experiment. Prefer starting v62c from
scratch or from a checkpoint whose metadata records:

```text
action_distribution = tanh_squashed_gaussian
```

## Recommended Next Work

Run a bounded v62c training chunk before any overnight or 60M+ maturation:

1. use online W&B;
2. keep `initial_log_std=-2.0` and `ent_coef=0.0`;
3. use `1024 envs x 32 steps`;
4. run about `10M` steps;
5. inspect milestone checkpoints, value/advantage scale, velocity error, and
   logprob consistency before deciding on longer training.

This support packet does not approve reward tuning or planner integration.
