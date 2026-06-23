# v37 Residual-GRU Transfer Preflight

Status: `passed`

Date: 2026-06-23

## Scope

This packet verifies the implementation gate for
`v37_gru_transfer_memory_structure_from_loop101`.

The target track remains unchanged:

- training config: `config/level3.toml`
- hard eval config: `config/level3.toml`
- track geometry/randomization change: forbidden
- controller: Level3 observation/history -> PPO Actor -> roll/pitch/yaw/thrust

## Transfer Design

The implemented policy architecture is:

```text
mlp_residual_recurrent_actor_gru256
```

It preserves the source MLP Actor and Critic from loop101, then adds a GRU-256
residual branch:

```text
action_mean = clamp(source_mlp_action_mean + gru_residual, -1, 1)
```

The residual output head is zero-initialized. Therefore the transferred policy
starts with the same deterministic action mean and value prediction as the
loop101 MLP checkpoint, while still allowing memory to learn during PPO.

## Source Checkpoint

```text
lsy_drone_racing/control/checkpoints/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m_final.ckpt
```

Checkpoint metadata:

- source policy arch: `mlp_2x_tanh`
- observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`
- hidden dim: `256`
- actor observation dim: `68`
- action dim: `4`

## Deterministic Parity

The real loop101 checkpoint was transferred into
`mlp_residual_recurrent_actor_gru256` and compared on zero, small random, and
standard random 68-dimensional observations.

Results:

- max deterministic action difference: `0.0`
- max value difference: `0.0`
- max logprob difference on source action: `0.0`
- max entropy difference: `0.0`
- residual head weight L1: `0.0`
- residual head bias L1: `0.0`

## Smoke Check

A 0-step training smoke run successfully built the Level3 environment, loaded
loop101, performed the MLP -> residual-GRU transfer, and saved a temporary
checkpoint:

```text
/tmp/level3_v37_transfer_smoke.ckpt
```

Smoke checkpoint metadata:

- policy arch: `mlp_residual_recurrent_actor_gru256`
- observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`
- recurrent hidden dim: `256`
- residual head weight L1: `0.0`

## Tests

Passed:

```text
pixi run -e tests python -m py_compile \
  lsy_drone_racing/control/ppo_level3_observation.py \
  lsy_drone_racing/control/train_CleanRL_ppo_level3.py \
  lsy_drone_racing/control/ppo_level3_inference.py \
  scripts/level3_ppo_loop.py

pixi run -e tests pytest -q \
  tests/unit/control/test_level3_v30_semantics_audit.py \
  tests/unit/control/test_level3_v33_gate_phase_reset.py \
  tests/unit/control/test_level3_v36_online_level_replay.py \
  tests/unit/control/test_level3_v37_gru_transfer_lane.py

pixi run ruff check --select I001,ANN001,ANN205 \
  lsy_drone_racing/control/ppo_level3_observation.py \
  lsy_drone_racing/control/train_CleanRL_ppo_level3.py \
  lsy_drone_racing/control/ppo_level3_inference.py \
  scripts/level3_ppo_loop.py \
  tests/unit/control/test_level3_v37_gru_transfer_lane.py
```

Summary:

- v37 lane registration uses the residual-GRU architecture.
- MLP transfer preserves deterministic action/value/logprob/entropy.
- residual-GRU checkpoint metadata round-trips correctly.
- done masks reset recurrent hidden state.
- v30/v33/v36 guard tests still pass.

## Dry Run

The orchestrator dry-run planned:

- trial: `level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight`
- initial checkpoint: loop101 final
- policy arch: `mlp_residual_recurrent_actor_gru256`
- train timesteps: `5_000_000`
- num envs: `256`
- num steps: `128`
- checkpoint interval: `1_000_000`
- eval milestones: `1,2,3,5`
- hard eval config: `level3.toml`

## Decision

The v37 support/preflight gate is satisfied. The next allowed action is one
bounded W&B-tracked loop iteration for
`v37_gru_transfer_memory_structure_from_loop101`, followed by analyzer,
exactly three reviews, a main-agent decision packet, commit, and push.
