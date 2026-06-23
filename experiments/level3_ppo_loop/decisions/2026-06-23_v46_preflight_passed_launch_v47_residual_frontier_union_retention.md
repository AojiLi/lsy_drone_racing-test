# Decision: V46 Preflight Passed, Launch V47 Residual Frontier Union Retention

Decision: `launch_named_structural_lane`

Resolved trial:
`level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m_analysis.md`

Prior v46 decision packet:
`experiments/level3_ppo_loop/decisions/2026-06-23_loop116_reject_v45_prepare_v46_residual_frontier_teacher_action_retention.md`

Approved next lane:

```text
v47_v5_residual_frontier_union_retention_mlp_from_loop110_3m
```

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not add MPC, planner, rule controller, inference-time safety shield,
  fallback controller, ensemble, or upper-level controller.
- Deployment remains:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

Teacher data and retention losses are training-only.

## Evidence

The v46 preflight packet passed:

```text
experiments/level3_ppo_loop/parity/2026-06-23_v46_residual_frontier_teacher_action_preflight.md
```

Observed parity:

- extracted-vs-direct scaled action diff: `0.0`;
- extracted-vs-direct hidden-state diff: `0.0`;
- residual branch contribution max: `0.043244`;
- diagnostic student-vs-teacher KL: `0.152496`;
- diagnostic action MSE: `0.040847`;
- diagnostic agreement within 0.15: `0.708604`.

This proves that loop107/v37 1M residual-GRU teacher action extraction includes
the residual branch and preserves recurrent hidden-state carry/reset semantics.

## Production Dataset

Built training-only loop107 residual-GRU teacher data:

```text
experiments/level3_ppo_loop/retention_datasets/v46_loop107_residual_teacher_success24_v5_student_loop110.npz
```

Source command:

```bash
pixi run -e gpu python scripts/build_v27_retention_dataset.py \
  --config level3.toml \
  --teacher-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_step_001000000.ckpt \
  --student-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_step_003000000.ckpt \
  --out experiments/level3_ppo_loop/retention_datasets/v46_loop107_residual_teacher_success24_v5_student_loop110.npz \
  --inference-module ppo_level3_inference \
  --seed-start 4501 \
  --max-seeds 240 \
  --target-successes 24 \
  --min-successes 8 \
  --max-samples 30000 \
  --exclude-seed-ranges 1-20,101-200,1001-1200
```

Loop107 residual source summary:

- samples: `8585`;
- successful train-pool trajectories: `24`;
- success seeds:
  `4501, 4506, 4509, 4512, 4526, 4537, 4541, 4548, 4563, 4570, 4582, 4617, 4620, 4632, 4634, 4637, 4659, 4672, 4702, 4709, 4718, 4721, 4728, 4729`.

Merged final v47 union dataset:

```text
experiments/level3_ppo_loop/retention_datasets/v46_loop107_loop101_loop110_frontier_success_union_v5.npz
```

This combines:

- v45 loop101/loop110 union: `48` successful trajectories, `15803` samples;
- v46 loop107 residual-GRU source: `24` successful trajectories, `8585`
  samples.

Final union summary:

- samples: `24388`;
- successful train-pool trajectories: `72`;
- student observation shape: `(24388, 68)`;
- teacher action shape: `(24388, 4)`;
- excluded seed overlap: `[]`.

Dataset audit:

```text
experiments/level3_ppo_loop/analysis/v46_residual_frontier_union_retention_dataset_audit.md
```

Audit metrics against the loop110/v39 3M MLP student:

- teacher agreement: `0.830296`;
- episode-min agreement: `0.658113`;
- episodes with agreement >=0.80: `36/72`;
- teacher KL: `0.083788`;
- action MSE: `0.017196`.

The generated `.npz`, `.json`, and `.csv` files remain local generated
artifacts and are ignored by git.

## Approved V47 Screen

Run exactly one bounded W&B-tracked train/evaluate chunk:

- initial checkpoint: loop110/v39 3M;
- train config: unchanged `config/level3.toml`;
- hard eval config: unchanged `config/level3.toml`;
- policy: `mlp_2x_tanh`;
- observation: `level3_target_gate_nearest_gate_2obs_local_history_v5`;
- reward numbers: fixed v39 gate-acquisition scale;
- retention: flat dataset KL with beta `0.03`;
- retention dataset:
  `experiments/level3_ppo_loop/retention_datasets/v46_loop107_loop101_loop110_frontier_success_union_v5.npz`;
- horizon: `5M`;
- checkpoint interval: `1M`;
- eval milestones: `1M,2M,3M,4M,5M`;
- W&B project: `ADR-PPO-Racing-Level3`.

## Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v47_v5_residual_frontier_union_retention_mlp_from_loop110_3m \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-23_level3_v46_residual_frontier_teacher_action_retention_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_v46_preflight_passed_launch_v47_residual_frontier_union_retention.md
```

After the chunk finishes, run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

Then use exactly three read-only reviews:

- evaluator metrics;
- W&B/PPO diagnostics;
- structure/research synthesis.

The main agent must write the next decision packet before any further training.

## Promotion / Rejection Rule

Promote or mature v47 only if it shows at least one of:

- validation success greater than `21%`;
- validation success `>=21%` with mean gates above `1.66/1.69` and crash
  `<=79%-80%`;
- clearly broader solved-seed coverage without losing the old frontier.

Reject or redesign v47 if it stays in the `18%-22%` plateau, merely reshuffles
solved seeds, or shows healthy retention metrics without hard-eval progress.
