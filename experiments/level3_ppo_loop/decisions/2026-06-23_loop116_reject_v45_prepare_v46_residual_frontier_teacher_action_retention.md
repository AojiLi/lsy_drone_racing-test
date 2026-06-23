# Decision: Reject V45 As Executed, Prepare V46 Residual Frontier Teacher Action Retention

Decision: `launch_named_structural_lane`

Resolved trial:
`level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m_analysis.md`

Subagent synthesis:
`experiments/level3_ppo_loop/analysis/level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m_subagent_reviews.md`

Approved next lane:

```text
v46_v5_residual_frontier_teacher_action_retention_preflight
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

Teacher data and retention losses may be used only during training.

## Evidence

v45 proved that the MLP retention lane is mechanically active:

- `retention/sampled_batch_size=512`;
- teacher KL improved to about `0.031`;
- teacher action MSE improved to about `0.005`;
- teacher agreement improved to about `0.946`.

But v45 did not improve hard eval:

| Milestone | Success | Mean Gates | Crash | Timeout | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1M | 15% | 1.56 | 85% | 0% | 6.901s |
| 2M | 14% | 1.46 | 86% | 0% | 6.486s |
| 3M | 17% | 1.56 | 83% | 0% | 6.925s |
| 4M | 20% | 1.60 | 80% | 0% | 6.941s |
| final | 19% | 1.59 | 81% | 0% | 6.880s |

The best checkpoint, 4M, is still below the frontier:

- loop107/v37 1M: `21%` success, `1.66` mean gates, `79%` crash,
  `7.578s` mean successful time;
- loop110/v39 3M: `21%` success, `1.64` mean gates, `79%` crash,
  `6.756s` mean successful time.

Subagent agreement:

- evaluator reviewer: v45 is a valid hard-eval experiment, but it does not
  clear the maturation gate and looks like seed reshuffle;
- W&B/PPO reviewer: retention is active and PPO is calm, so the failure is not
  classic PPO instability;
- structure reviewer: the next useful question is whether loop107/v37 1M, the
  actual global frontier, can be safely used as a residual-GRU teacher.

## Diagnosis

v45 is not a train-longer case. It preserved a familiar `18%-21%` plateau while
showing healthy retention metrics. This suggests the loop101/loop110 MLP
teacher union does not contain enough coverage to expand the frontier.

The missing teacher is loop107/v37 1M, but loop107 uses
`mlp_residual_recurrent_actor_gru256`. Before using it for retention data, the
loop must prove that extracted teacher actions include the residual branch and
correct recurrent hidden-state carry/reset behavior.

## Approved V46 Scope

`v46_v5_residual_frontier_teacher_action_retention_preflight`

First action:

- implement or audit residual-GRU teacher action extraction;
- compare dataset-extracted actions against direct inference actions;
- verify recurrent hidden-state resets at episode boundaries;
- verify recurrent hidden-state carry through ordered teacher trajectories;
- build a small loop107 diagnostic retention dataset on disjoint train-pool
  seeds;
- keep generated `.npz`, checkpoints, W&B dirs, logs, and CSVs out of git;
- write a parity packet before training.

Only after the preflight passes may v46 run a bounded 5M W&B-tracked training
screen. That training screen should still evaluate on unchanged
`config/level3.toml`.

## Not Approved

- Do not continue or mature v45 as executed.
- Do not start future training from loop116 final.
- Do not use loop107/v37 1M as a teacher until residual-GRU action extraction
  parity passes.
- Do not launch training from v46 before a parity packet exists.
- Do not alter `config/level3.toml`.

## Promotion / Rejection Rule

Promote or mature v46 only if it shows at least one of:

- validation success greater than `21%`;
- validation success `>=21%` with mean gates above `1.66/1.69` and crash
  `<=79%-80%`;
- clear broader solved-seed coverage without losing the old frontier.

Reject or redesign v46 if it stays in the `18%-22%` plateau, merely reshuffles
solved seeds, or shows healthy retention metrics without evaluator progress.
