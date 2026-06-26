# v61 Brax-Style Rollout Benchmark

Date: 2026-06-27

## Purpose

The user rejected the SBX route because it was too slow. This benchmark removes
the SBX trainer path and tests whether a pure JAX/Brax-style rollout can beat
the current PyTorch v60 fast path.

This is a rollout probe, not a PPO training run. It does not change
`config/level3.toml`, does not evaluate Level3 success, and does not create a
qualified tracker checkpoint.

## Code Changes

Removed:

```text
lsy_drone_racing/control/train_level3_reference_tracker_sbx.py
sbx-rl dependency
```

Added:

```text
scripts/benchmark_v60_brax_rollout.py
```

The benchmark uses:

- existing JAX race env `_step`;
- `brax.envs.base.State` as the rollout state container;
- JAX `lax.scan` for rollout;
- JAX v60 dense command generator;
- JAX command-v3 observation builder;
- JAX clean no-gate command reward;
- small JAX MLP policy for action generation.

It keeps the v60 contract:

- task semantics: `reference_command_no_gate_reward`
- observation semantics: `level3_reference_tracker_command_v3`
- no gate/aperture/finish/race-progress/stage-progress reward
- unchanged `config/level3.toml`

## Benchmark Commands

Pure JAX/Brax-style rollout:

```bash
pixi run -e gpu python scripts/benchmark_v60_brax_rollout.py \
  --config level3_tracker_free_space.toml \
  --seed 26084 \
  --num-envs 1024 \
  --num-steps 32 \
  --repeat 10 \
  --jax-device gpu
```

PyTorch v60 fast-path comparison:

```bash
/usr/bin/time -f 'elapsed=%E cpu=%P maxrss_kb=%M' \
  pixi run -e gpu python lsy_drone_racing/control/train_level3_reference_tracker_ppo.py \
  --config level3_tracker_free_space.toml \
  --task reference_command_no_gate_reward \
  --seed 26086 \
  --total-timesteps 1048576 \
  --num-envs 1024 \
  --num-steps 32 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --model-path /tmp/v60_pytorch_fastpath_1m_compare.ckpt \
  --cuda \
  --jax-device gpu
```

## Results

Pure JAX/Brax-style rollout, `1024 envs x 32 steps`:

```text
compile_plus_first_run_s: 13.960
run_times_s:
  [10.676, 0.02050, 0.02056, 0.02036, 0.02057,
   0.02042, 0.02023, 0.02034, 0.02048, 0.02038]
median_run_s: 0.02045
median_steps_per_s: 1,602,338 env steps/s
done_mean_last: 0.0088
```

The first timed run after compilation is still slow, likely GPU backend
autotuning or deferred compilation. After that, rollouts are stable around
`0.020s` for `32768` env steps.

PyTorch v60 fast path, `1,048,576` env steps:

```text
elapsed: 26.34s
throughput: about 39,810 env steps/s
```

Single-update PyTorch cold-start smoke:

```text
32768 env steps
elapsed: 18.01s
```

This cold-start number is mostly startup/compile overhead and should not be
used as the main comparison.

## Interpretation

The pure JAX/Brax-style rollout path is promising. Its warmed-up rollout is far
faster than the current PyTorch fast path. The important caveat is that the
benchmark only proves rollout speed:

```text
policy MLP + action scale + race env step + v60 reference/obs/reward
```

It does not yet include:

```text
PPO advantage computation
PPO minibatch updates
checkpoint save/load
W&B logging
evaluation script compatibility
```

Therefore, do not launch long training from this benchmark. The next step is a
real Brax PPO trainer/checkpoint adapter using this rollout representation.
Promotion should require a bounded PPO smoke and a checkpoint/evaluator path,
then compare end-to-end steps/s against the PyTorch v60 fast path.
