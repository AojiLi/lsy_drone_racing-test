# Level3 V46 Residual Frontier Teacher Action Retention Plan

Status: structural preflight packet. Do not launch training from this packet
alone.

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

Teacher data, teacher actions, and retention losses are training-only. They
must not become inference-time planners, shields, fallback controllers,
ensembles, or upper-level controllers.

## Local Evidence

v45 showed that flat MLP retention can be active without improving hard eval:

- best v45 checkpoint: `20%` success, `1.60` mean gates, `80%` crash,
  `6.941s` mean successful time;
- final v45 checkpoint: `19%` success, `1.59` mean gates, `81%` crash;
- teacher KL improved to about `0.031`;
- teacher action MSE improved to about `0.005`;
- teacher agreement improved to about `0.946`.

The result did not beat either frontier checkpoint:

- loop107/v37 1M: `21%` success, `1.66` mean gates, `79%` crash,
  `7.578s` mean successful time;
- loop110/v39 3M: `21%` success, `1.64` mean gates, `79%` crash,
  `6.756s` mean successful time.

The v45 teacher union used compatible v5 MLP teachers from loop101 and loop110.
It did not include loop107, the global corrected-loop frontier, because loop107
uses `mlp_residual_recurrent_actor_gru256`. Existing flat dataset extraction
must not assume that residual-GRU teacher actions are identical to a simple MLP
action head.

## Hypothesis

```text
v46_v5_residual_frontier_teacher_action_retention_preflight
```

The useful frontier may require teacher actions from loop107/v37 1M. Before
using those actions in a retention dataset, the loop must prove that the data
builder extracts the actual deployed residual-GRU action distribution:

- recurrent hidden state is reset at episode boundaries;
- hidden state is carried through each teacher trajectory in order;
- teacher action means include the residual branch;
- teacher log standard deviation matches inference/training metadata;
- recorded student observations remain the v5 local-obstacle observation used
  by the MLP student;
- generated seeds exclude dev, validation, and final seed ranges.

## Required Preflight

Before any v46 PPO training:

1. Add or audit residual-GRU teacher rollout extraction for
   `mlp_residual_recurrent_actor_gru256`.
2. Build a small diagnostic dataset from loop107/v37 1M on disjoint train-pool
   seeds.
3. Compare extracted teacher actions against direct `ppo_level3_inference`
   actions on the same ordered trajectories.
4. Verify recurrent hidden-state reset/carry behavior with deterministic tests.
5. Verify finite teacher KL, action MSE, agreement, and nonzero sampled batch
   size when the dataset is attached to a v5 MLP student.
6. Write a parity packet under `experiments/level3_ppo_loop/parity/`.
7. Run `scripts/level3_ppo_loop.py --dry-run` for the v46 structural
   hypothesis and confirm it does not start training before the preflight is
   attached.

## Possible Training Screen After Preflight

Only if the preflight passes, the first bounded screen should use:

- initial checkpoint: loop110/v39 3M MLP;
- train config: unchanged `config/level3.toml`;
- hard eval config: unchanged `config/level3.toml`;
- policy: `mlp_2x_tanh`;
- observation: `level3_target_gate_nearest_gate_2obs_local_history_v5`;
- reward numbers: v39 gate-acquisition scale;
- retention: flat MLP dataset KL, with a union dataset that includes
  loop107 residual-GRU teacher actions plus the existing loop101/loop110 MLP
  teachers;
- horizon: bounded 5M screen before any maturation;
- checkpoint interval: 1M;
- W&B logging required.

## Promotion / Rejection Rule

Promote only if v46 shows at least one of:

- validation success greater than `21%`;
- validation success `>=21%` with mean gates above `1.66/1.69` and crash
  `<=79%-80%`;
- clearly broader solved-seed coverage without losing the old frontier.

Reject or redesign if it again stays in the `18%-22%` band, merely reshuffles
success seeds, or shows healthy retention metrics without hard-eval progress.
