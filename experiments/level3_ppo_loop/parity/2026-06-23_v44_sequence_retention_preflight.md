# V44 Sequence Retention Preflight

Status: passed.

Approved lane:

```text
v44_sequence_success_retention_failure_correction_gru_v10
```

Decision packet:
`experiments/level3_ppo_loop/decisions/2026-06-23_loop114_reject_v43_prepare_v44_sequence_retention.md`

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- No Level3 track geometry, gate layout, obstacle layout, or randomization
  changed.
- No MPC, planner, rule controller, inference-time shield, fallback
  controller, or upper-level controller is added.
- Teacher data is training-only. Deployment remains:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

## Dataset

Built:
`experiments/level3_ppo_loop/retention_datasets/v44_loop110_train_pool_success24_v5_teacher_v10_student.npz`

This file is a local generated artifact and is ignored by git through the
repository `*.npz` rule.

Build command:

```bash
pixi run -e gpu python scripts/build_v27_retention_dataset.py \
  --config level3.toml \
  --teacher-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt \
  --student-checkpoint lsy_drone_racing/control/checkpoints/level3_v43_success_trajectory_bc_warmstart/level3_v43_success_trajectory_bc_warmstart.ckpt \
  --out experiments/level3_ppo_loop/retention_datasets/v44_loop110_train_pool_success24_v5_teacher_v10_student.npz \
  --inference-module ppo_level3_inference \
  --seed-start 3001 \
  --max-seeds 240 \
  --target-successes 24 \
  --min-successes 8 \
  --max-samples 30000 \
  --exclude-seed-ranges 1-20,101-200,1001-1200
```

Dataset summary:

- config: `level3.toml`
- teacher: loop110/v39 3M feed-forward policy
- student checkpoint/layout source: v43 BC warmstart / v10 observation
- samples: `7761`
- success trajectories: `24`
- student observation shape: `(7761, 91)`
- teacher action shape: `(7761, 4)`
- excluded ranges: `1-20`, `101-200`, `1001-1200`
- success seeds:
  `3001, 3028, 3043, 3049, 3054, 3058, 3059, 3065, 3072, 3073, 3086, 3088, 3090, 3105, 3118, 3124, 3126, 3130, 3136, 3140, 3162, 3170, 3176, 3179`

## Retention Loss Preflight

The real v44 dataset was loaded through
`load_v27_retention_dataset` with `policy_arch=recurrent_actor_gru256`,
`recurrent_sequence_len=128`, and `v27_retention_batch_size=512`.

Observed preflight values:

- retention samples: `7761`
- retention sequences: `24`
- sampled batch size: `512`
- teacher KL: `111.632881`
- teacher action MSE: `0.323411`
- teacher agreement: `0.282227`
- GRU actor gradient norm after `teacher_kl.backward()`: `2625.102777`

This proves the v44 path samples sequence batches, produces finite retention
metrics, and backpropagates into the recurrent Actor. This specifically fixes
the loop114/v43 failure mode where W&B showed retention inactive with
`retention/sampled_batch_size=0`.

## Tests

Passed:

```bash
pixi run -e tests python -m pytest -q \
  tests/unit/control/test_level3_recurrent_retention_dataset.py \
  tests/unit/control/test_level3_v43_bc_warmstart.py
```

Result:

```text
2 passed
```

Passed:

```bash
pixi run -e tests python -m py_compile \
  lsy_drone_racing/control/train_CleanRL_ppo_level3.py \
  scripts/level3_ppo_loop.py \
  tests/unit/control/test_level3_recurrent_retention_dataset.py
```

## Dry Run

Passed:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v44_sequence_success_retention_failure_correction_gru_v10 \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_114_structural_v43_success_trajectory_bc_warmstart_gru_v10_10m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-23_level3_v43_success_trajectory_imitation_warmstart_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop114_reject_v43_prepare_v44_sequence_retention.md
```

Planned trial:

```text
level3_loop_115_structural_v44_sequence_success_retention_gru_v10_5m
```

Planned training support:

- initial checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_v43_success_trajectory_bc_warmstart/level3_v43_success_trajectory_bc_warmstart.ckpt`
- train/eval config: `level3.toml`
- policy arch: `recurrent_actor_gru256`
- observation layout: `level3_gate_corridor_aperture_margin_2obs_local_history_v10`
- train timesteps: `5_000_000`
- checkpoint interval: `1_000_000`
- eval milestones: `1M,2M,3M,4M,5M`
- `v27_teacher_kl_beta=0.03`
- `v27_retention_batch_size=512`

## Launch Decision

V44 is cleared for exactly one bounded W&B-tracked train/evaluate chunk. After
the run, execute the analyzer, then use exactly three read-only reviews:
evaluator metrics, W&B/PPO diagnostics, and structure/research synthesis.
The main agent must write the next decision packet before any further training.
