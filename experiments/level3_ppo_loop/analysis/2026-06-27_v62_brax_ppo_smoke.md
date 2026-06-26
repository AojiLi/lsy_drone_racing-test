# v62 Brax/Optax PPO Smoke

Date: 2026-06-27

## Purpose

Turn the v61 pure-JAX/Brax-style rollout probe into a minimal trainable PPO
loop for the v60 clean command tracker:

- JAX actor-critic policy;
- JAX race-env rollout using `brax.envs.base.State`;
- GAE and clipped PPO update with Optax;
- checkpoint write/read verification;
- W&B logging;
- deterministic short smoke eval.

This is a backend smoke, not a tracker-skill acceptance run and not a Level3
hard eval.

## Command

```bash
pixi run -e gpu python scripts/train_v60_brax_ppo_smoke.py \
  --config level3_tracker_free_space.toml \
  --seed 26101 \
  --num-envs 1024 \
  --num-steps 32 \
  --total-timesteps 262144 \
  --num-minibatches 4 \
  --update-epochs 1 \
  --checkpoint-path /tmp/v62_brax_ppo_smoke.pkl \
  --wandb-enabled \
  --wandb-mode offline \
  --wandb-project-name ADR-PPO-Racing-Level3 \
  --wandb-run-name v62_brax_ppo_smoke \
  --wandb-run-id v62_brax_ppo_smoke_20260627 \
  --jax-device gpu
```

## Result

- Checkpoint: `/tmp/v62_brax_ppo_smoke.pkl`
- Checkpoint verification: loaded successfully; format
  `v62_brax_ppo_smoke`, `global_step=262144`, `obs_dim=56`.
- W&B offline run:
  `wandb/offline-run-20260627_015039-v62_brax_ppo_smoke_20260627`
- `all_finite`: `1.0` for all training updates.
- Final deterministic smoke eval:
  - `eval/reward_mean`: `-2.7849`
  - `eval/done_mean`: `0.0`
  - `eval/command_position_error`: `0.3078`
  - `eval/command_velocity_error`: `0.9445`
  - `eval/cross_track_error`: `0.2023`
  - `eval/action_abs_mean`: `0.0920`

## Speed

The first two updates include JAX compilation/autotune cost:

- update 1: `22.44s`, `1.46k env steps/s`
- update 2: `16.55s`, `1.98k env steps/s`

After compilation, steady-state updates were:

| Update | Time | Env steps/s | Ratio vs PyTorch fast path |
|---:|---:|---:|---:|
| 3 | `0.0301s` | `1.089M` | `27.36x` |
| 4 | `0.0254s` | `1.292M` | `32.46x` |
| 5 | `0.0248s` | `1.324M` | `33.26x` |
| 6 | `0.0248s` | `1.323M` | `33.24x` |
| 7 | `0.0246s` | `1.334M` | `33.52x` |
| 8 | `0.0252s` | `1.300M` | `32.66x` |

Script steady-state summary:

- `steady_state_steps_per_s`: `1.270M`
- `steady_state_vs_pytorch_ratio`: `31.92x`

Comparison baseline: PyTorch v60 fast path smoke was about `39.8k env steps/s`.

## Checks

```bash
pixi run -e tests python -m py_compile scripts/train_v60_brax_ppo_smoke.py
pixi run -e tests python -m ruff check scripts/train_v60_brax_ppo_smoke.py scripts/benchmark_v60_brax_rollout.py
pixi run -e tests python -m ruff format --check scripts/train_v60_brax_ppo_smoke.py
pixi run -e tests python -m pytest tests/unit/control/test_level3_reference_tracker_env.py -q
```

Results:

- `py_compile`: passed
- `ruff check`: passed
- `ruff format --check`: passed
- tracker env tests: `33 passed`

## Interpretation

The pure JAX route is viable. The smoke proves that the v60 command-tracker
rollout can be trained end-to-end with a PPO-style update while remaining
device-resident after compilation. The speed win is large enough to justify
turning this smoke into a real trainer path.

The current script is intentionally minimal. It does not yet replace the
production tracker trainer because it lacks full trainer ergonomics,
milestone-checkpoint management, resume support, evaluator integration, and
formal stage-gate reporting. It also has not yet proven learning quality at
1M-8M tracker budgets.

## Next Action

Promote this into a v62 trainer lane only after a builder/checker gate:

1. Convert the smoke script into a maintained tracker backend or shared module.
2. Add milestone checkpoint/resume support and W&B online defaults.
3. Add a bounded 1M command-tracker run to verify learning signal, not just
   plumbing.
4. Keep `config/level3.toml` unchanged and keep v60 no-gate reward semantics.
