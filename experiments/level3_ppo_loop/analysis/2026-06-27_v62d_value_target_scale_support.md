# v62d Value Target Scale Support

Date: 2026-06-27

## Scope

This is a builder/checker-gated support packet for the first v62d candidate.
The change is deliberately narrow:

```text
critic network output predicts returns / value_target_scale
GAE and advantages remain in raw reward units
policy action path remains tanh_squashed_gaussian
reward, observation, reference generator, and configs are unchanged
```

No Level3 track geometry was changed. No gate, aperture, race-progress,
finish, obstacle, or stage reward was added.

## Builder Change

Files changed:

- `scripts/train_v60_brax_ppo_smoke.py`
- `scripts/train_v62_brax_reference_command_tracker.py`
- `scripts/audit_v62b_brax_ppo_signals.py`
- `tests/unit/scripts/test_v62_value_target_scaling.py`

New trainer argument:

```text
--value-target-scale
```

When the scale is `S`, the rollout values used for GAE are converted back to
raw reward units:

```text
raw_value = scaled_value * S
raw_next_value = scaled_next_value * S
```

The critic target stored in the PPO update batch is then:

```text
value_target = return / S
```

This reduces critic target magnitude without changing rewards, advantages, or
policy-loss semantics.

## Smoke Evidence

Command:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_value_target_scale_smoke \
  --config level3_tracker_free_space.toml \
  --seed 26401 \
  --num-envs 128 \
  --num-steps 32 \
  --total-timesteps 32768 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 32768 \
  --checkpoint-path /tmp/v62d_value_target_scale_smoke.pkl \
  --summary-json /tmp/v62d_value_target_scale_smoke_summary.json \
  --action-distribution tanh_squashed_gaussian \
  --value-target-scale 50.0 \
  --eval-rollouts 1 \
  --jax-device gpu
```

Result:

| Metric | Initial | Final |
|---|---:|---:|
| reward | -2.2685 | -2.0558 |
| command position error | 0.2272 | 0.1986 |
| command velocity error | 0.8844 | 0.7725 |
| cross-track error | 0.1949 | 0.1635 |
| done mean | 0.0 | 0.0 |

Last train diagnostics included:

```text
value_target_scale = 50.0
value_loss = 0.4654
returns_mean = -65.3761
value_targets_mean = -1.3075
value_target_abs_mean = 1.3075
explained_variance = 0.1016
all_finite = 1.0
action clip fraction = 0.0
stored-vs-env logprob abs mean ~= 3.29e-7
```

## Audit Evidence

Command:

```bash
pixi run -e gpu python scripts/audit_v62b_brax_ppo_signals.py \
  --config level3_tracker_free_space.toml \
  --seed 26402 \
  --num-envs 128 \
  --num-steps 32 \
  --checkpoint /tmp/v62d_value_target_scale_smoke.pkl \
  --initial-log-std-values=-2.0 \
  --action-distribution tanh_squashed_gaussian \
  --output /tmp/v62d_value_target_scale_smoke_audit.json \
  --jax-device gpu
```

Checkpoint audit result:

| Check | Result |
|---|---|
| value target scale read from checkpoint | `50.0` |
| action clipping | `ok` |
| action sampling/logprob | `ok` |
| advantage scale | `ok` |
| initial/policy std | `ok` |
| reward scale | `ok` |
| stored-vs-env logprob abs mean | `3.09e-7` |

The initial-policy comparison with scale `1.0` still reports large raw
advantages, which is expected and is the reason v62d_001 tests scaled critic
targets.

## Local Checks

Commands already run:

```bash
pixi run -e tests pytest tests/unit/scripts/test_v62_value_target_scaling.py -q
pixi run -e tests ruff check scripts/train_v60_brax_ppo_smoke.py scripts/train_v62_brax_reference_command_tracker.py scripts/audit_v62b_brax_ppo_signals.py tests/unit/scripts/test_v62_value_target_scaling.py
pixi run -e tests ruff format --check scripts/train_v60_brax_ppo_smoke.py scripts/train_v62_brax_reference_command_tracker.py scripts/audit_v62b_brax_ppo_signals.py tests/unit/scripts/test_v62_value_target_scaling.py
git diff --check
git diff --name-only HEAD -- config/level3.toml config/level3_tracker_free_space.toml
```

Status:

```text
pytest: passed
ruff check: passed
ruff format --check: passed after formatting
git diff --check: passed
config diff: empty
```

## Checker Result

Read-only checker result:

```text
ALL GREEN
```

The checker verified:

- GAE stays in raw reward units;
- only critic targets are scaled;
- tanh-squashed action/logprob semantics are preserved;
- `reference_command_no_gate_reward` and
  `level3_reference_tracker_command_v3` remain unchanged;
- `config/level3.toml` and `config/level3_tracker_free_space.toml` have no diff;
- local pytest, ruff, format, and `git diff --check` pass.

## Decision

Support was clean enough to launch `v62d_001` as a full 30M from-scratch
candidate.
