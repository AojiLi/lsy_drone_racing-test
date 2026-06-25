# V55 Tracker Decision: Switch Maturation To Vectorized PPO

Created: 2026-06-25

Decision: `launch_tracker_structural_fix`

Stage: `hover`

## Decision

Stop using the old single-env tracker PPO path for learning chunks.

Use vectorized PPO for tracker maturation:

```text
default: 1024 envs x 32 steps = 32768 samples/update
fallback/variant: 256 envs x 128 steps = 32768 samples/update
```

The default for the next hover maturation retry is:

```text
--num-envs 1024
--num-steps 32
--total-timesteps 1000000
--checkpoint-interval 250000
```

## Evidence

The interrupted single-env hover maturation attempt wrote only one milestone:

```text
lsy_drone_racing/control/checkpoints/v55_tracker_qualification/hover/v55_tracker_hover_maturation_attempt001_step_000250000.ckpt
```

It took roughly 11 minutes to reach 250k env steps. That is too slow for a
12-stage loop and does not match the repo's previous PPO training setup.

Earlier Level2/Level3 PPO training used vectorized rollouts, commonly
`1024 envs x 32 steps`. The tracker trainer previously lacked the equivalent
support.

## Implemented Fix

Implemented vector tracker support in:

```text
lsy_drone_racing/control/level3_reference_tracker.py
lsy_drone_racing/control/train_level3_reference_tracker_ppo.py
```

The tracker trainer now supports:

```text
--num-envs / --num_envs
--jax-device
```

and stores PPO rollout buffers as `[num_steps, num_envs, ...]`.

## Validation

`1024 x 32` smoke passed on GPU:

```text
global_step = 32768
num_envs = 1024
num_steps = 32
jax_device = gpu
```

The smoke checkpoint was written to `/tmp`, not committed.

## Next Action

After read-only checker approval, rerun hover maturation as a new vectorized
attempt. Do not use the aborted single-env checkpoint to decide tracker
learning quality.

If `1024 x 32` produces W&B/milestone signs of insufficient credit horizon,
write a new decision packet before switching to `256 x 128`.
