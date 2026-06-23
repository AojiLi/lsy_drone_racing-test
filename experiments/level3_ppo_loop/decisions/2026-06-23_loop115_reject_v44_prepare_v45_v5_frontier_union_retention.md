# Decision: Reject V44 As Executed, Prepare V45 V5 Frontier Union Retention

Decision: `launch_named_structural_lane`

Resolved trial:
`level3_loop_115_structural_v44_sequence_success_retention_gru_v10_5m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_115_structural_v44_sequence_success_retention_gru_v10_5m_analysis.md`

Subagent synthesis:
`experiments/level3_ppo_loop/analysis/level3_loop_115_structural_v44_sequence_success_retention_gru_v10_5m_subagent_reviews.md`

Approved next lane:

```text
v45_v5_frontier_seed_union_retention_mlp_from_loop110_3m
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

Teacher data, retention data, and distillation losses may be used only during
training. They are not part of inference.

## Evidence

v44 fixed the mechanical failure from v43:

- recurrent sequence retention loaded `7761` samples from `24` trajectories;
- `retention/sampled_batch_size=512`;
- train-log teacher KL improved from about `23.48` to `20.05`;
- train-log teacher action MSE improved from about `0.0392` to `0.0232`;
- teacher agreement improved from about `0.680` to `0.756`.

But v44 failed its hard-eval promotion rule:

| Milestone | Success | Mean Gates | Crash | Timeout |
| --- | ---: | ---: | ---: | ---: |
| 1M | 0% | 0.13 | 94% | 6% |
| 2M | 0% | 0.06 | 80% | 20% |
| 3M | 0% | 0.07 | 95% | 5% |
| 4M | 0% | 0.11 | 96% | 4% |
| final | 0% | 0.17 | 95% | 5% |

The final `0.17` mean gates is only marginally above the BC-only diagnostic
of `0.15`, with no successes and mostly gate-0 failures. That is not a
maturation signal.

The global frontier remains loop107/v37 1M:

- success: `21%`;
- mean gates: `1.66`;
- crash rate: `79%`;
- mean successful time: `7.578s`.

loop110/v39 3M ties the success frontier with better successful time:

- success: `21%`;
- mean gates: `1.64`;
- crash rate: `79%`;
- mean successful time: `6.756s`.

## Diagnosis

Reviewer agreement:

- evaluator reviewer: v44 has no hard-eval success and is not a maturation
  candidate;
- W&B/PPO reviewer: retention is active and PPO is not exploding, but training
  signals do not convert into validation progress;
- structure reviewer: GRU/v10 is now a negative sequence across v40/v42/v43/v44,
  so the next route should step back to the stronger v5/frontier path.

This is not a reward-only follow-up and not a train-longer case for v44.

## Approved V45 Scope

`v45_v5_frontier_seed_union_retention_mlp_from_loop110_3m`

Hypothesis:

The useful v5 frontier is seed-coverage limited and prone to churn. A
training-only union retention dataset from compatible v5 MLP frontier teachers
can preserve known successful behavior while PPO continues from the fastest
frontier MLP checkpoint, loop110/v39 3M.

First implementation:

- deployed policy: single `mlp_2x_tanh` PPO Actor;
- observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`;
- initial checkpoint: loop110/v39 3M;
- train/eval config: unchanged `config/level3.toml`;
- reward numbers: keep v39 gate-acquisition scale;
- retention: flat MLP dataset KL, beta `0.03`;
- teachers for the first dataset: loop110/v39 3M and loop101/v33 final;
- generated train-pool retention data must exclude dev, validation, and final
  seed ranges.

loop107/v37 1M remains the hard-eval frontier to beat. Do not use loop107 as a
retention-data teacher until residual-GRU action extraction is explicitly
preflighted; otherwise the dataset builder can silently miss the residual
branch.

Required preflight before training:

1. Build or audit the v45 union retention dataset with v5 student observations.
2. Verify finite teacher KL/MSE/agreement and nonzero sampled batch size on the
   real dataset.
3. Run a dry-run of the v45 structural command.
4. Confirm no generated `.npz`, checkpoints, W&B dirs, logs, or CSVs are added
   to git.

## Not Approved

- Do not continue or mature v44 checkpoints.
- Do not start future training from loop115 checkpoints.
- Do not run another GRU/v10 lane without a new decision packet.
- Do not make a narrow reward-only follow-up to v44.
- Do not alter `config/level3.toml`.

## Promotion / Rejection Rule

Promote or mature v45 only if it shows at least one of:

- validation success greater than `21%`;
- validation success `>=21%` with mean gates above `1.66/1.69` and crash
  `<=79%-80%`;
- clear broader solved-seed coverage without losing the old frontier.

Reject or redesign v45 if it stays in the `18%-22%` plateau, merely reshuffles
success seeds, or shows healthy retention metrics without hard-eval progress.
