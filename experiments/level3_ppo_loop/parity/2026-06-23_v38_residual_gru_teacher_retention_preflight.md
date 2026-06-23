# V38 Residual-GRU Teacher Retention Preflight

Status: passed. This packet clears the support gate for:

```text
v38_gru_teacher_retention_distillation_from_loop107_1m
```

## Scope

- Student start checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_step_001000000.ckpt`
- Teacher checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m_final.ckpt`
- Train config: unchanged `config/level3.toml`.
- Hard eval config: unchanged `config/level3.toml`.
- Actor observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Deployment remains end-to-end PPO Actor only:
  observation/history -> PPO Actor -> roll/pitch/yaw/thrust.
- No Level3 track geometry, gate, obstacle, or randomization files were changed.

## Implemented Support

- Added online teacher sampling for residual-GRU students.
- Kept old MLP `.npz` retention-dataset path intact for historical v27 lanes.
- Wired retention KL into recurrent PPO minibatches.
- Logged:
  - `losses/teacher_kl`
  - `losses/teacher_action_mse`
  - `retention/teacher_agreement`
  - `retention/sampled_batch_size`
- Wrote teacher-retention provenance into checkpoints under
  `teacher_retention`.

## Tests

Commands run:

```bash
pixi run -e tests python -m py_compile \
  lsy_drone_racing/control/train_CleanRL_ppo_level3.py \
  lsy_drone_racing/control/ppo_level3_observation.py \
  scripts/level3_ppo_loop.py

pixi run -e tests pytest -q \
  tests/unit/control/test_level3_v37_gru_transfer_lane.py

pixi run -e tests pytest -q \
  tests/unit/control/test_level3_v30_semantics_audit.py \
  tests/unit/control/test_level3_v33_gate_phase_reset.py \
  tests/unit/control/test_level3_v36_online_level_replay.py \
  tests/unit/control/test_level3_v37_gru_transfer_lane.py

pixi run -e tests ruff check --select I001,ANN001,ANN205 \
  lsy_drone_racing/control/train_CleanRL_ppo_level3.py \
  lsy_drone_racing/control/ppo_level3_observation.py \
  scripts/level3_ppo_loop.py \
  tests/unit/control/test_level3_v37_gru_transfer_lane.py
```

Results:

- v37/v38 focused tests: `9 passed`.
- broader Level3 unit tests: `29 passed`, with the existing JAX overflow cast
  warnings in gate/reset wrappers.
- ruff selected checks: passed.

## Tiny Training Smoke

Command shape:

- config: `level3.toml`
- student initial checkpoint: loop107 1M residual-GRU
- teacher checkpoint: loop101 final MLP
- policy arch: `mlp_residual_recurrent_actor_gru256`
- total timesteps: `8`
- num envs: `2`
- num steps: `4`
- W&B: disabled
- output checkpoint: `/tmp/level3_v38_retention_smoke.ckpt`

Result:

```text
v27 retention teacher_kl=0.013017 teacher_action_mse=0.004420 teacher_agreement=0.8750 sampled_batch_size=4.0
Training for 8 steps took 6.97 seconds.
model saved to /tmp/level3_v38_retention_smoke.ckpt
```

The smoke run proves the retention branch is executed inside the real recurrent
PPO training loop, not only in isolated unit tests.

Smoke checkpoint metadata includes:

```json
{
  "beta": 0.08,
  "enabled": true,
  "retention_batch_size": 4,
  "retention_dataset_path": null,
  "source": "online_teacher",
  "teacher_observation_layout": "level3_target_gate_nearest_gate_2obs_local_history_v5",
  "teacher_policy_arch": "mlp_2x_tanh"
}
```

## Real Checkpoint Retention Probe

The preflight loaded the real loop107 1M residual-GRU student and real loop101
MLP teacher, then computed online teacher retention on a deterministic
synthetic recurrent minibatch.

Result:

```json
{
  "finite": true,
  "sampled_batch_size": 16,
  "student_layout": "level3_target_gate_nearest_gate_2obs_local_history_v5",
  "student_policy_arch": "mlp_residual_recurrent_actor_gru256",
  "student_recurrent_hidden_dim": 256,
  "teacher_action_mse": 0.0008859977824613452,
  "teacher_agreement": 1.0,
  "teacher_kl": 0.005217831581830978,
  "teacher_layout": "level3_target_gate_nearest_gate_2obs_local_history_v5",
  "teacher_policy_arch": "mlp_2x_tanh"
}
```

This satisfies the v38 requirement for nonzero retention sampling and finite
teacher KL/action MSE/agreement metrics before training.

## Dry Run

Command run:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --structural-hypothesis v38_gru_teacher_retention_distillation_from_loop107_1m \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_108_structural_v37b_residual_gru_mature_loop107_1m_2m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop108_reject_plain_v37_prepare_v38_retention.md
```

Dry-run result:

- status: `planned`
- proposal:
  `structural_v38_gru_teacher_retention_loop107_1m_preflight`
- train config: `level3.toml`
- eval config: `level3.toml`
- initial checkpoint: loop107 1M residual-GRU
- teacher checkpoint: loop101 final MLP
- training horizon: `2_000_000`
- checkpoint interval: `500_000`
- eval milestones: `0.5,1,1.5,2`

## Next Command

The bounded v38 screen may now be launched. After it completes, run the
analyzer, use the three required reviews, and write a main-agent decision packet
before any next training chunk.
