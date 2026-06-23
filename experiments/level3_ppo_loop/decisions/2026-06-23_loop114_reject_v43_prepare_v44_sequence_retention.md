# Decision: Reject V43 As Executed, Prepare V44 Sequence Retention

Decision: `launch_named_structural_lane`

Resolved trial:
`level3_loop_114_structural_v43_success_trajectory_bc_warmstart_gru_v10_10m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_114_structural_v43_success_trajectory_bc_warmstart_gru_v10_10m_analysis.md`

Subagent synthesis:
`experiments/level3_ppo_loop/analysis/level3_loop_114_structural_v43_success_trajectory_bc_warmstart_gru_v10_10m_subagent_reviews.md`

Approved next lane:

```text
v44_sequence_success_retention_failure_correction_gru_v10
```

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not add MPC, planner, rule controller, inference-time safety shield,
  fallback controller, or upper-level controller.
- Deployment remains:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

Teacher data, replay data, and imitation losses may be used only during
training. They are not part of inference.

## Evidence

loop114/v43 failed its promotion rule:

- best analyzer checkpoint: `5M`;
- success: `0/100`;
- mean gates: `0.01`;
- crash rate: `51%`;
- timeout rate: `49%`;
- failures: `99%` at gate 0 and `1%` at gate 1.

The highest gate-progress milestone was 9M:

- success: `0/100`;
- mean gates: `0.06`;
- crash rate: `71%`.

BC-only diagnostic before PPO:

- success: `0/100`;
- mean gates: `0.15`;
- failure reached gate1/gate2 on 12 validation seeds.

Therefore PPO fine-tuning did not preserve the useful part of the BC signal.
It reduced the already-small first-gate conversion instead of improving it.

The global frontier remains loop107 1M:

- success: `21%`;
- mean gates: `1.66`;
- crash rate: `79%`;
- mean successful time: `7.578s`.

## Diagnosis

Reviewer agreement:

- evaluator reviewer: reject loop114; no milestone is a maturation candidate;
- W&B/PPO reviewer: no explosive PPO instability, but PPO updates were
  under-effective and unanchored; active teacher retention was off
  (`retention/sampled_batch_size=0`);
- structure reviewer: v41 ruled out obvious GRU/v10 wiring bugs and v43
  preflight proved supervised imitation, so loop114 is a BC-to-PPO handoff
  failure.

This is not a reward-only follow-up and not a train-longer case.

## Approved V44 Scope

`v44_sequence_success_retention_failure_correction_gru_v10`

Hypothesis:

One-shot BC warmstart is too fragile. PPO needs active sequence-level
retention/rehearsal of successful train-pool behavior, plus broader train-pool
failure-correction coverage, while keeping the deployed policy as a single PPO
Actor.

Required preflight before training:

1. Build or audit a larger disjoint train-pool success dataset with v10
   student observations, excluding dev_seen, validation_unseen, and
   final_locked seed ranges.
2. Implement or verify recurrent sequence retention during PPO:
   nonzero sampled batch size, finite teacher KL/MSE/agreement, hidden-state
   reset at sequence starts, and no teacher dependency at inference.
3. Optionally add train-pool failure-correction data only as training support,
   not as deployment logic.
4. Run a short preflight proving retention batches are sampled and loss terms
   are active before any long PPO training.
5. If preflight passes, launch exactly one bounded W&B-tracked train/evaluate
   chunk with milestone hard eval on unchanged `config/level3.toml`.

## Not Approved

- Do not continue or mature loop114 checkpoints.
- Do not run another v43 PPO chunk without active retention or a new decision
  packet.
- Do not use loop114 checkpoints as future starting points.
- Do not make a narrow reward-only follow-up to loop114.
- Do not alter `config/level3.toml`.

## Promotion / Rejection Rule

Promote v44 if it shows at least one of:

- nonzero hard-eval success;
- mean gates above `0.5`;
- a clear improvement over the BC-only `0.15` mean-gates diagnostic;
- active retention metrics that convert into validation_unseen gate progress.

Reject or redesign v44 if active retention remains below BC-only gate progress,
fails to sample retention batches, or improves W&B losses without hard-eval
gate conversion.
