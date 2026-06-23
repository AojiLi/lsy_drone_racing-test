# Decision: Continue v37 From loop107 1M as v37b

Decision: `continue_same_hypothesis`

Pending gate resolved by this packet:

- trial:
  `level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight`
- analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_analysis.md`
- subagent synthesis:
  `experiments/level3_ppo_loop/analysis/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_subagent_reviews.md`

Approved next lane:

```text
v37b_residual_gru_maturation_from_loop107_1m
```

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization to make the metric easier.
- Do not continue from loop107 final.
- Do not start future v37 continuation from loop107 2M, 3M, 4M, or final unless
  a later decision packet explicitly approves it.
- Keep deployment as:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is approved by this packet.

## Evidence

loop107 tested residual-GRU transfer from loop101 final for 5M.

Best loop107 checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight/level3_loop_107_structural_v37_gru_transfer_memory_loop101_preflight_step_001000000.ckpt`
- success: `21/100`
- mean gates: `1.66`
- crash rate: `79%`
- mean successful time: `7.578s`

Later loop107 checkpoints drifted downward:

| Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| 1M | 21% | 1.66 | 79% | 7.578s |
| 2M | 15% | 1.55 | 85% | 7.463s |
| 3M | 12% | 1.46 | 88% | 7.313s |
| 4M | 12% | 1.40 | 88% | 6.705s |
| final | 17% | 1.51 | 83% | 7.202s |

Compared with loop101 final, loop107 1M slightly improves success and crash
rate, but not mean gates or time:

- loop101 final: `20%` success, `1.69` mean gates, `80%` crash, `6.873s`;
- loop107 1M: `21%` success, `1.66` mean gates, `79%` crash, `7.578s`.

## Reviewer Synthesis

- Evaluator reviewer: do not continue v37 as-is. The 1M checkpoint has a small
  hard-eval signal, but later checkpoints degrade.
- W&B/PPO reviewer: PPO does not look unstable. KL and clip fraction are very
  small, entropy is stable, value loss decreases, and explained variance
  improves. The issue is weak conversion and possible under-updating or drift,
  not optimizer explosion.
- Structure reviewer: keep v37 alive only by maturing the 1M checkpoint with
  dense milestone evals. If it drifts again, move to retention/distillation.

## Approved v37b Scope

`v37b_residual_gru_maturation_from_loop107_1m`

- Initial checkpoint:
  loop107 1M checkpoint listed above.
- Train config:
  unchanged `config/level3.toml`.
- Hard eval config:
  unchanged `config/level3.toml`.
- Actor observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Controller:
  end-to-end PPO Actor only.
- Actor architecture:
  `mlp_residual_recurrent_actor_gru256`.
- Training horizon:
  short `2M` continuation, not long maturation.
- Checkpoint/eval strategy:
  `500k`, `1M`, `1.5M`, and `2M` milestones; final is not assumed best.

## Not Approved

- Do not continue v37 from loop107 final.
- Do not tune reward numbers as the immediate next action.
- Do not change `config/level3.toml`.
- Do not launch 30M/60M maturation for v37 unless a later v37b result clearly
  improves both success and mean gates.
- Do not add retention/distillation in this lane; if needed, make it a separate
  named structural lane.

## Promotion / Rejection Rule

Promote v37 only if v37b improves beyond loop107 1M and loop101 on hard eval,
preferably by improving both success and mean gates.

Reject or escalate to retention/distillation if v37b fails to reproduce or beat
`21%` success and remains contact-dominated around `1.6-1.7` mean gates.
