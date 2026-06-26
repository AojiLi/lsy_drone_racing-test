# v61 Packaged PPO Backend Probe

Date: 2026-06-27

## Purpose

Test the user's request to prefer mature installed packages over a hand-written
JAX PPO trainer for the v60 clean command tracker.

This probe does not change `config/level3.toml`, does not launch a learning
run, and does not evaluate Level3 success. It only checks package availability,
trainer plumbing, W&B logging, and rough throughput.

## Dependency Result

Installed/confirmed in the `gpu` environment:

- `sbx-rl 0.27.0`
- `brax 0.14.2`
- `wandb 0.28.0`
- `stable_baselines3 2.9.0`
- `torch 2.8.0`

The first `pixi add --feature rl sbx-rl` attempt created a separate
`[dependency-groups] rl` entry and temporarily dropped the real W&B SDK from
the `gpu` environment. This was corrected by moving both `sbx-rl` and `brax`
into the existing `[project.optional-dependencies].rl` list and reinstalling
the `gpu` environment.

## Implemented Backend

Added:

```text
lsy_drone_racing/control/train_level3_reference_tracker_sbx.py
```

This script uses SBX's packaged JAX PPO implementation and a thin
`ReferenceTrackerSBXVecEnv` adapter around the existing
`ReferenceTrackerVectorEnv`. It keeps the v60 tracker semantics:

- task: `reference_command_no_gate_reward`
- observation layout: `level3_reference_tracker_command_v3`
- no gate, aperture, finish, race-progress, stage-progress, or obstacle reward
  terms in the v60 command reward path
- unchanged `config/level3.toml`

The earlier draft file
`lsy_drone_racing/control/train_level3_reference_tracker_ppo_jax.py` was
removed so the loop does not mix a custom PPO implementation with the package
backend route.

## Smoke Results

Small SBX smoke:

```text
16 envs x 8 steps, total_timesteps=256, W&B offline
result: passed
reported fps: about 138
model: /tmp/v61_sbx_tracker_smoke.zip
```

1024-env SBX smoke with W&B offline:

```text
1024 envs x 32 steps, total_timesteps=32768, update_epochs=1
result: passed
reported fps: about 4115
elapsed: 22.82s
model: /tmp/v61_sbx_tracker_1024_smoke.zip
```

1024-env SBX smoke without W&B:

```text
1024 envs x 32 steps, total_timesteps=32768, update_epochs=1
result: passed
reported fps: about 4570
elapsed: 17.65s
model: /tmp/v61_sbx_tracker_1024_nowandb_smoke.zip
```

W&B offline logging now works with the real package after the dependency fix.

## Verification

```text
pixi run -e tests python -m py_compile lsy_drone_racing/control/train_level3_reference_tracker_sbx.py
pixi run -e tests python -m ruff check lsy_drone_racing/control/train_level3_reference_tracker_sbx.py tests/unit/control/test_level3_reference_tracker_env.py
pixi run -e tests python -m ruff format --check lsy_drone_racing/control/train_level3_reference_tracker_sbx.py
pixi run -e tests python -m pytest tests/unit/control/test_level3_reference_tracker_env.py -q
```

Result:

```text
33 passed, 2 warnings
```

## Interpretation

SBX is a usable packaged PPO backend, but it is not the speed solution. On the
same v60 tracker environment, the recent PyTorch fast-path smoke reached about
`36k` env steps/s, while SBX reached only about `4.6k` env steps/s in the
1024-env single-update smoke without W&B.

The likely cause is that SBX still interacts through the SB3 VecEnv/Python
adapter boundary. It removes custom PPO update code, but it does not make the
rollout loop fully device-resident.

Brax is now installed and is the better package candidate for the real
long-term speed fix because its PPO trainer expects a pure JAX
`brax.envs.base.Env` and performs rollout/update inside JAX. The next v61 step
should be a minimal Brax adapter for the v60 command tracker:

```text
RaceCore EnvData + JAX reset/step
JAX v60 dense command generator
JAX command-v3 observation
JAX ReferenceCommandReward
↓
Brax PPO train smoke
```

Do not launch a long SBX training run as the main speed route unless there is a
specific reason to value package simplicity over throughput.
