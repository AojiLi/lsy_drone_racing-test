# Level3 V45 V5 Frontier Union Retention Plan

Status: structural research packet for the next Level3 PPO support lane.

## Scope

Final acceptance remains hard evaluation on unchanged `config/level3.toml`:

- success rate `>= 0.60`;
- mean successful time `<= 7.0s`;
- no Level3 track geometry, gate layout, obstacle layout, or randomization
  changes.

Deployment remains a single end-to-end PPO Actor:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield,
fallback controller, ensemble, or upper-level controller is part of this lane.
Teacher data is training-only.

## Local Evidence

The GRU/v10 sequence has now been tested enough to draw a local conclusion:

| Lane | Result |
| --- | --- |
| v40 true GRU/v10 from scratch | `0%` success, `0.0` mean gates |
| v41 wiring audit | train/eval parity and reset/carry checks passed |
| v42 GRU/v10 gate-phase reset curriculum | `0%` success, best `0.01` mean gates |
| v43 GRU/v10 BC warmstart | BC-only `0.15` mean gates, PPO erased signal |
| v44 GRU/v10 active sequence retention | retention active, final `0.17` mean gates, `0%` success |

The failure is therefore not simply inactive retention or an obvious GRU/v10
wiring bug. The retained successful states do not create robust normal-start
first-gate behavior for the v10 GRU policy.

The current useful frontier is still v5:

- loop107/v37 1M: `21%` success, `1.66` mean gates, `79%` crash,
  `7.578s` mean successful time;
- loop110/v39 3M: `21%` success, `1.64` mean gates, `79%` crash,
  `6.756s` mean successful time.

loop107 uses a residual-GRU policy, while loop110 uses the compatible v5
`mlp_2x_tanh` policy. Because the existing flat dataset-retention trainer is
already proven for MLP students, v45 starts from the loop110/v39 MLP frontier
and uses compatible MLP teacher rollouts first.

## Hypothesis

```text
v45_v5_frontier_seed_union_retention_mlp_from_loop110_3m
```

The 19%-21% plateau may be partly caused by seed-coverage churn: new training
recovers some solved seeds but loses others. A train-pool union retention
dataset from compatible v5 frontier teachers can act as an anti-drift anchor
while PPO continues from the best fast MLP checkpoint, loop110/v39 3M.

The first v45 screen should not change the deployed observation, controller
family, or reward numbers. It should test whether explicit retention of
successful v5 frontier behaviors preserves existing competence while online PPO
searches for additional validation seeds.

## First Implementation

Use only teacher checkpoints whose action distribution is extracted correctly
by the existing dataset builder:

- loop110/v39 3M MLP frontier;
- loop101/v33 final MLP gate-phase-reset frontier.

Do not use loop107/v37 residual-GRU as a dataset teacher until the data builder
has a separate preflight proving residual actions include the residual branch.
loop107 remains the validation frontier to beat.

Dataset requirements:

- `config=level3.toml`;
- student observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`;
- student checkpoint: loop110/v39 3M;
- disjoint train-pool seeds;
- exclude `1-20`, `101-200`, and `1001-1200`;
- store `student_obs`, `teacher_action_mean`, and `teacher_action_logstd`;
- keep the generated `.npz` ignored by git.

## First PPO Screen

If preflight passes:

- initial checkpoint: loop110/v39 3M;
- train config: unchanged `config/level3.toml`;
- hard eval config: unchanged `config/level3.toml`;
- policy: `mlp_2x_tanh`;
- observation: `level3_target_gate_nearest_gate_2obs_local_history_v5`;
- reward numbers: v39 gate-acquisition scale;
- retention: flat MLP dataset KL with beta `0.03`;
- horizon: `5M`;
- checkpoint interval: `1M`;
- hard-eval milestones: `1M, 2M, 3M, 4M, 5M`;
- W&B logging required.

Promotion gate:

- exceed `21%` validation success; or
- preserve `>=21%` success while improving mean gates beyond `1.66/1.69` and
  keeping crash `<=79%-80%`; or
- produce clearly broader solved-seed coverage without losing the old frontier.

Reject if it remains a seed reshuffle in the `18%-22%` band without better mean
gates or lower crash, or if retention metrics look healthy but hard eval does
not improve.
