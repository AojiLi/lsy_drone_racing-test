# V45 V5 Frontier Union Retention Preflight

Status: passed.

Approved lane:

```text
v45_v5_frontier_seed_union_retention_mlp_from_loop110_3m
```

Decision packet:
`experiments/level3_ppo_loop/decisions/2026-06-23_loop115_reject_v44_prepare_v45_v5_frontier_union_retention.md`

Research packet:
`experiments/level3_ppo_loop/research/2026-06-23_level3_v45_v5_frontier_union_retention_plan.md`

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- No Level3 track geometry, gate layout, obstacle layout, or randomization
  changed.
- No MPC, planner, rule controller, inference-time shield, fallback
  controller, ensemble, or upper-level controller is added.
- Teacher data is training-only. Deployment remains:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

## Dataset

Built final union dataset:

```text
experiments/level3_ppo_loop/retention_datasets/v45_loop101_loop110_frontier_success_union_v5.npz
```

This file and its source `.npz` files are local generated artifacts and are
ignored by git through the repository `*.npz` rule.

Source A: loop110/v39 3M MLP teacher

```bash
pixi run -e gpu python scripts/build_v27_retention_dataset.py \
  --config level3.toml \
  --teacher-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt \
  --student-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt \
  --out experiments/level3_ppo_loop/retention_datasets/v45_loop110_teacher_success24_v5_student_loop110.npz \
  --inference-module ppo_level3_inference \
  --seed-start 4001 \
  --max-seeds 240 \
  --target-successes 24 \
  --min-successes 8 \
  --max-samples 30000 \
  --exclude-seed-ranges 1-20,101-200,1001-1200
```

Source B: loop101/v33 final MLP teacher

```bash
pixi run -e gpu python scripts/build_v27_retention_dataset.py \
  --config level3.toml \
  --teacher-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m/level3_loop_101_structural_v33_gate_phase_reset_curriculum_loop097_12m_10m_final.ckpt \
  --student-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt \
  --out experiments/level3_ppo_loop/retention_datasets/v45_loop101_teacher_success24_v5_student_loop110.npz \
  --inference-module ppo_level3_inference \
  --seed-start 4301 \
  --max-seeds 240 \
  --target-successes 24 \
  --min-successes 8 \
  --max-samples 30000 \
  --exclude-seed-ranges 1-20,101-200,1001-1200
```

Dataset summary:

- config: `level3.toml`
- student checkpoint/layout source: loop110/v39 3M / v5 observation
- student observation shape: `(15803, 68)`
- teacher action shape: `(15803, 4)`
- samples: `15803`
- success trajectories: `48`
- teacher sources: `2`
- source sample counts:
  - loop110/v39 3M: `7389`
  - loop101/v33 final: `8414`
- excluded ranges: `1-20`, `101-200`, `1001-1200`
- source success seeds:
  - loop110 source:
    `4001, 4007, 4019, 4022, 4023, 4032, 4054, 4057, 4065, 4069, 4070, 4073, 4076, 4091, 4093, 4095, 4096, 4099, 4117, 4121, 4139, 4140, 4141, 4148`
  - loop101 source:
    `4301, 4304, 4308, 4311, 4320, 4322, 4324, 4326, 4331, 4346, 4366, 4370, 4376, 4377, 4382, 4385, 4388, 4390, 4393, 4409, 4416, 4437, 4438, 4439`

## Retention Loss Preflight

The real v45 union dataset was loaded through `load_v27_retention_dataset`
with `policy_arch=mlp_2x_tanh`, `v27_teacher_kl_beta=0.03`, and
`v27_retention_batch_size=512`.

Observed preflight values:

- retention samples: `15803`
- sampled batch size: `512`
- teacher KL: `100.218346`
- teacher action MSE: `0.261363`
- teacher agreement: `0.283203`
- MLP actor gradient norm after `teacher_kl.backward()`: `2367.377743`

This proves the v45 path can load the union dataset, sample nonzero flat MLP
retention batches, produce finite metrics, and backpropagate into the Actor.

## Dry Run

Passed before this packet was attached:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v45_v5_frontier_seed_union_retention_mlp_from_loop110_3m \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_115_structural_v44_sequence_success_retention_gru_v10_5m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-23_level3_v45_v5_frontier_union_retention_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop115_reject_v44_prepare_v45_v5_frontier_union_retention.md
```

Planned trial:

```text
level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m
```

Planned training support:

- initial checkpoint: loop110/v39 3M
- train/eval config: `level3.toml`
- policy arch: `mlp_2x_tanh`
- observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`
- train timesteps: `5_000_000`
- checkpoint interval: `1_000_000`
- eval milestones: `1M,2M,3M,4M,5M`
- `v27_teacher_kl_beta=0.03`
- `v27_retention_batch_size=512`

## Launch Decision

V45 is cleared for exactly one bounded W&B-tracked train/evaluate chunk after
this preflight packet is committed and pushed. After the run, execute the
analyzer, then use exactly three read-only reviews: evaluator metrics,
W&B/PPO diagnostics, and structure/research synthesis. The main agent must
write the next decision packet before any further training.
