# v62 Brax Reference-Command Tracker 1M Learning-Signal Run

Date: 2026-06-27

## Purpose

Promote the v62 Brax/Optax PPO smoke into a formal bounded lane:

```text
v62_brax_reference_command_tracker
```

This run answers three questions:

1. Does speed remain high after adding formal lane plumbing?
2. Are PPO loss, KL, entropy, and reward numerically sane?
3. Do deterministic eval metrics show a positive learning signal after 1M
   environment steps?

This is not a Level3 hard eval and not a tracker-stage pass.

## New Training Entry

```text
scripts/train_v62_brax_reference_command_tracker.py
```

It reuses the v61/v62 JAX rollout and PPO building blocks but adds lane-level
training features:

- lane metadata: `v62_brax_reference_command_tracker`;
- default `1,048,576` step bounded run;
- milestone checkpoints;
- final checkpoint;
- resume-capable checkpoint format;
- W&B logging;
- deterministic pre/post eval on the same generated reference setup;
- summary JSON.

The lane keeps v60 clean-tracker semantics:

```text
level3_reference_tracker_command_v3
reference_command_no_gate_reward
no gate/aperture/obstacle/race/finish/stage reward
```

## Command

```bash
pixi run -e gpu python scripts/train_v62_brax_reference_command_tracker.py \
  --config level3_tracker_free_space.toml \
  --seed 26202 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 1048576 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-interval 262144 \
  --wandb-enabled \
  --wandb-mode offline \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-run-name v62_brax_reference_command_tracker_1m \
  --wandb-run-id v62_brax_reference_command_tracker_1m_20260627 \
  --jax-device gpu
```

## Artifacts

- Final checkpoint:
  `lsy_drone_racing/control/checkpoints/v62_brax_reference_command_tracker/v62_brax_reference_command_tracker_final.pkl`
- Milestone checkpoints:
  - `..._step_000262144.pkl`
  - `..._step_000524288.pkl`
  - `..._step_000786432.pkl`
  - `..._step_001048576.pkl`
- Summary JSON:
  `experiments/level3_ppo_loop/analysis/tracker_stage_metrics/v62_brax_reference_command_tracker_1m_summary.json`
- W&B offline run:
  `wandb/offline-run-20260627_020028-v62_brax_reference_command_tracker_1m_20260627`

Checkpoint load verification passed:

```text
format = v62_brax_reference_command_tracker
global_step = 1048576
lane_name = v62_brax_reference_command_tracker
obs_dim = 56
```

## Speed Answer

Yes, speed remains high after engineering the formal lane.

The first two updates include compile/autotune:

| Update | Env steps/s |
|---:|---:|
| 1 | `2.12k` |
| 2 | `2.11k` |

After compile, updates ran mostly around `1.15M-1.36M env steps/s`.

Script summary:

```text
steady_state_steps_per_s = 1.3047M
steady_state_vs_pytorch_ratio = 32.78x
```

The old PyTorch v60 fast path baseline was about `39.8k env steps/s`.

## PPO Diagnostics Answer

PPO did not numerically explode:

- `train/all_finite = 1.0` throughout;
- final `approx_kl = 0.000248`;
- final `clip_fraction = 0.0`;
- entropy stayed around `3.68 -> 3.70`;
- policy loss stayed near zero.

However, this is not a healthy learning result yet:

- value loss stayed very large, ending at `6502.87`;
- grad norm grew to `641.32`;
- rollout reward became more negative than the first update;
- rollout tracking errors increased substantially before partially settling.

So the backend is stable enough to run, but the learning setup is not yet good
enough to promote to long maturation.

## Eval Learning-Signal Answer

No positive deterministic eval learning signal was observed after 1M steps.

| Metric | Initial Eval | Final Eval | Delta | Better? |
|---|---:|---:|---:|---|
| reward_mean | `-3.3313` | `-7.2119` | `-3.8806` | no |
| command_position_error | `0.5496` | `0.6459` | `+0.0963` | no |
| command_velocity_error | `0.6065` | `1.5760` | `+0.9694` | no |
| cross_track_error | `0.4548` | `0.5189` | `+0.0640` | no |
| done_mean | `0.0` | `0.0078` | `+0.0078` | no |
| action_abs_mean | `0.0206` | `0.1795` | `+0.1589` | no |

The script's summary flag was:

```text
has_eval_learning_signal = false
```

## Interpretation

The engineering lane is successful, but the current PPO learning configuration
is not.

The clearest pattern is:

```text
initial deterministic policy is very small-action and mediocre,
training increases action magnitude,
rollout errors and value targets get large,
deterministic eval becomes worse after 1M.
```

Likely next suspects:

- exploration/action distribution mismatch: PPO log-prob is computed on the
  unclipped Gaussian sample while the environment sees clipped actions;
- initial log std or entropy pressure is too high for a delicate tracker task;
- reward/return scale is too large for the current critic/update settings;
- no observation/reward normalization yet in this Brax lane;
- the 32-step rollout may be too short for the full command sequence, even
  though it is fast.

## Decision

Do not launch an 8M or longer v62/v60 maturation run from this configuration.

Next work should be a v62b learning-signal fix, not a longer run:

1. Add a smaller-exploration or squashed-action PPO variant, or at minimum run
   `initial_log_std <= -1.5` and lower entropy pressure.
2. Add reward scaling or return/value normalization support.
3. Keep the same 1M bounded learning-signal gate.
4. Promote only if deterministic eval reward/tracking errors improve without
   sacrificing the `~1M+ env steps/s` speed advantage.

## Checks

```bash
pixi run -e tests python -m py_compile scripts/train_v62_brax_reference_command_tracker.py
pixi run -e tests python -m ruff check scripts/train_v62_brax_reference_command_tracker.py scripts/train_v60_brax_ppo_smoke.py scripts/benchmark_v60_brax_rollout.py
pixi run -e tests python -m ruff format --check scripts/train_v62_brax_reference_command_tracker.py
pixi run -e tests python -m pytest tests/unit/control/test_level3_reference_tracker_env.py -q
```

Results:

- `py_compile`: passed
- `ruff check`: passed
- `ruff format --check`: passed
- tracker env tests: `33 passed`

`config/level3.toml` was not modified.
