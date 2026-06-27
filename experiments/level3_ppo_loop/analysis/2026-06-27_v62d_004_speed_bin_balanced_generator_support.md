# v62d_004 Speed-Bin Balanced Generator Support

Date: 2026-06-27

## Purpose

Implement builder/checker support for the next v62d candidate:

```text
v62d_004_speed_bin_balanced_generator
```

This is Family C: generator velocity distribution. It changes the clean
reference-command generator only when explicitly enabled. It does not launch
the 30M training run by itself.

## Hypothesis

v62d_003 showed that doubling the generic velocity-error reward coefficient is
not sufficient. The best checkpoint improved velocity error by only `2.4%` and
made action smoothness materially worse. The next useful single-family knob is
to change what the tracker sees during training:

```text
more explicit speed bins
longer constant-speed windows
longer brake ramps
longer low-speed-through segments
longer recover-speed transitions
stricter spacing consistency with desired_speed * dt
```

## Implemented Support

New command generator profile:

```text
speed_bin_balanced
```

Default behavior remains:

```text
command_generator_profile=default
```

Touched files:

```text
scripts/benchmark_v60_brax_rollout.py
scripts/train_v60_brax_ppo_smoke.py
scripts/train_v62_brax_reference_command_tracker.py
scripts/audit_v62b_brax_ppo_signals.py
```

The new profile is exposed as:

```bash
--command-generator-profile speed_bin_balanced
```

It is passed into:

- initial tracker state creation;
- episode reset plan sampling inside the PPO env step;
- formal v62 training checkpoint metadata and summary;
- audit rollout reconstruction.

## Generator Differences

Compared with the default generator, `speed_bin_balanced` samples wider and
more deliberate speed bins:

```text
hold/brake: 0.00-0.06 m/s
approach-decelerate entry: 0.10-0.24 m/s
low-speed-through: 0.20-0.42 m/s
steady pass-through: 0.45-0.82 m/s
recover-speed: 0.40-0.82 m/s
```

It also lengthens key segments:

```text
hold_steps: randomized 44-72
pass_decel_min_steps: 34
slow_min_steps: 54
recover_min_steps: 48
decel_fraction: 0.42
```

This makes the reference stream spend more time in the behaviors v62d needs to
teach: prepare-to-brake, hold, low-speed-through, and smooth recovery.

## Builder Checks

Commands run:

```bash
pixi run -e gpu python -m py_compile \
  scripts/benchmark_v60_brax_rollout.py \
  scripts/train_v60_brax_ppo_smoke.py \
  scripts/train_v62_brax_reference_command_tracker.py \
  scripts/audit_v62b_brax_ppo_signals.py
```

Result:

```text
passed
```

Default equivalence check:

```text
sample_command_plans(key, origin, dt)
sample_command_plans(key, origin, dt, "default")
max_delta = 0.0
```

Generator stats check showed `speed_bin_balanced` has longer mean windows:

| Metric | default mean | speed_bin mean |
|---|---:|---:|
| pass_steps | 38.3 | 65.1 |
| hold_steps | 36.0 | 58.1 |
| slow_steps | 47.3 | 85.9 |
| recover_steps | 47.1 | 59.6 |
| total_steps | 168.7 | 268.7 |

Tiny trainer smoke:

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --lane-name v62d_004_speed_bin_balanced_generator_support_smoke \
  --config level3_tracker_free_space.toml \
  --seed 26441 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 32768 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 32768 \
  --checkpoint-path /tmp/v62d_004_speed_bin_balanced_generator_support_smoke.pkl \
  --summary-json /tmp/v62d_004_speed_bin_balanced_generator_support_smoke.json \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --value-target-scale 1.0 \
  --eval-rollouts 1 \
  --jax-device gpu
```

Result:

```text
passed
all_finite = 1.0
action clipping = 0.0
action/logprob consistency ~= 3.21e-7
summary command_generator_profile = speed_bin_balanced
checkpoint metadata command_generator_profile = speed_bin_balanced
```

Tiny audit smoke:

```bash
pixi run -e gpu python scripts/audit_v62b_brax_ppo_signals.py \
  --config level3_tracker_free_space.toml \
  --seed 26442 \
  --num-envs 256 \
  --num-steps 32 \
  --checkpoint /tmp/v62d_004_speed_bin_balanced_generator_support_smoke.pkl \
  --initial-log-std-values=-2.0 \
  --action-distribution tanh_squashed_gaussian \
  --command-generator-profile speed_bin_balanced \
  --output /tmp/v62d_004_speed_bin_balanced_generator_support_audit.json \
  --jax-device gpu
```

Result:

```text
passed
command_generator_profile = speed_bin_balanced
action_sampling_logprob = ok
action_clipping = ok
initial_std = ok
reward_scale = ok
```

The one-update checkpoint audit reported `advantage_scale=large` by a tiny
margin (`abs(mean) ~= 25.3`); this is not treated as a training-quality gate for
the 32k plumbing smoke.

## Checker Result

Independent read-only checker result:

```text
ALL GREEN
```

Checker evidence:

- profile is exposed and gated in `scripts/benchmark_v60_brax_rollout.py`;
- `default` is the CLI default and speed-bin behavior only activates with
  `speed_bin_balanced`;
- trainer, formal lane, and audit all pass the selected profile into initial
  state and episode reset plan sampling where relevant;
- checkpoint metadata records `command_generator_profile=speed_bin_balanced`;
- default omitted profile and explicit `default` produce identical sampled
  plans;
- tiny speed-bin smoke passes;
- `py_compile` passes for touched scripts;
- `git diff --check` passes;
- both `config/level3.toml` and `config/level3_tracker_free_space.toml` are
  unchanged.

## Boundaries

Preserved:

```text
config/level3.toml unchanged
config/level3_tracker_free_space.toml unchanged
actor observation remains level3_reference_tracker_command_v3
action_distribution remains tanh_squashed_gaussian
no gate/aperture/race/finish/stage reward
no gate/obstacle/planner-phase actor inputs
default generator profile remains available
```

## Approved Next Training Command

After this support packet and commit, v62d_004 may train from scratch with:

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
