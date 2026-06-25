# v55 Tracker Vectorized PPO Support

Date: 2026-06-25

## Reason

The first `hover` maturation attempt used the tracker trainer's old single-env
PPO path:

```text
num_envs = 1
num_steps = 256
total_timesteps = 1M
```

It wrote the `250k` milestone after roughly 11 minutes and had not reached
`500k` before interruption. This is too slow for the 12-stage tracker loop and
does not match the repository's prior successful PPO training pattern.

Earlier Level2/Level3 PPO runs used vectorized rollout geometry, especially:

```text
1024 envs x 32 steps = 32768 samples/update
```

The tracker trainer therefore needed native vectorized rollout support before
continuing stage maturation.

## Implemented

Added `ReferenceTrackerVectorEnv` in:

```text
lsy_drone_racing/control/level3_reference_tracker.py
```

It wraps Gymnasium's vectorized JAX race env and keeps per-world tracker state:

- per-world `ReferenceTrajectoryGenerator`;
- per-world `TrackerMemory`;
- per-world reference/reward calculation;
- batched tracker observations;
- mean tracker diagnostics for W&B.

Updated:

```text
lsy_drone_racing/control/train_level3_reference_tracker_ppo.py
```

The trainer now accepts:

```text
--num-envs / --num_envs
--jax-device
```

and uses PPO buffers shaped as:

```text
[num_steps, num_envs, ...]
```

`global_step` now counts environment interactions:

```text
global_step += num_envs
```

Checkpoint metadata records `num_envs`, `num_steps`, `total_timesteps`, and
`jax_device`.

## Validation

Static/unit validation:

```bash
pixi run -e tests ruff check \
  lsy_drone_racing/control/level3_reference_tracker.py \
  lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  tests/unit/control/test_level3_reference_tracker_env.py
```

Result: passed.

```bash
pixi run -e tests python -m pytest \
  tests/unit/control/test_level3_reference_tracker_env.py -q
```

Result: `6 passed`.

Trainer smoke:

```bash
pixi run -e gpu python -m lsy_drone_racing.control.train_level3_reference_tracker_ppo \
  --config level3_tracker_free_space.toml \
  --task hover \
  --tracker-env-mode free_space \
  --seed 560102 \
  --total-timesteps 32768 \
  --num-envs 1024 \
  --num-steps 32 \
  --num-minibatches 8 \
  --update-epochs 1 \
  --learning-rate 3e-4 \
  --hidden-dim 64 \
  --max-episode-steps 64 \
  --checkpoint-interval 32768 \
  --model-path /tmp/v55_tracker_vector1024_smoke.ckpt \
  --jax-device gpu \
  --cuda
```

Result: passed in about 16 seconds.

Checkpoint metadata:

```json
{
  "global_step": 32768,
  "num_envs": 1024,
  "num_steps": 32,
  "total_timesteps": 32768,
  "jax_device": "gpu",
  "task": "hover"
}
```

## Operational Decision

Do not continue tracker stage maturation with the old single-env command.

Default tracker maturation command geometry is now:

```text
--num-envs 1024 --num-steps 32
```

If W&B curves or milestone evaluation suggest the short temporal horizon hurts a
stage, use a main-agent decision packet to switch that stage to:

```text
--num-envs 256 --num-steps 128
```

which keeps the same `32768` samples per PPO update while giving each world a
longer contiguous trajectory.

## Next Action

Rerun `hover` maturation attempt 001 or 002 with:

```text
--total-timesteps 1000000
--num-envs 1024
--num-steps 32
--checkpoint-interval 250000
```

Then evaluate milestone checkpoints and run the stage gate checker. The aborted
single-env `250k` checkpoint is a timing diagnostic only and should not be used
to decide tracker learning.
