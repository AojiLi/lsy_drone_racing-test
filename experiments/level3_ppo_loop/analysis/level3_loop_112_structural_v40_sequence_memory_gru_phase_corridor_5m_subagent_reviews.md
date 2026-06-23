# Level3 Loop112 Subagent Reviews

Trial:
`level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m_analysis.md`

## Evaluator Metrics

Key finding:
v40 should not be matured as-is. None of its milestone checkpoints are
promising.

Evidence:

- 1M, 2M, 3M, 4M, and final all reached `0/100` success.
- All five checkpoints recorded `0.0` mean gates.
- All failures were at target gate 0.
- The nominal best checkpoint was 3M, but only because it had lower crash
  (`52%`) and higher timeout (`48%`), not because it solved any gate.
- The pre-v40 frontier remains loop101/loop107/loop110 at roughly `20%-21%`
  success and `1.64-1.69` mean gates.

Recommended next action:
Reject `v40_sequence_memory_gru_phase_corridor_from_scratch` as-is. Do not run
30M/60M maturation and do not continue from loop112 checkpoints.

Risk / rollback:
Do not treat lower crash plus higher timeout as progress. State best must
remain the pre-v40 frontier checkpoint.

## W&B / PPO Diagnostics

Key finding:
v40 did not form effective policy learning. The evidence looks more like an
actor-update, recurrent-training, action-scale, or observation/inference
sanity issue than a simple reward-number miss.

Evidence:

- Hard eval best: `0%` success, `0.0` mean gates, `52%` crash, `48%` timeout.
- PPO tail metrics showed `approx_kl=0.0`, `clipfrac=0.0`, and
  `policy_loss=-7e-06`, indicating almost no late actor movement.
- `entropy=0.708` stayed flat, while `explained_variance=0.001243` and
  `value_loss=1105.996` show the critic did not explain returns.
- `race/passed_gate_rate=3.1e-05`, `race/finished_rate=0.0`, and
  `race/gate_stage=0.004089` did not convert into evaluator gate progress.

Recommended next action:
Run a named PPO/GRU/action-wiring diagnostic lane before any further GRU/v10
training. Check recurrent rollout/update gradients, log_std and entropy,
train/eval action scaling parity, recurrent hidden-state inference parity, v10
observation numeric ranges, single-batch overfit, and zero-update parity.

Risk / rollback:
If diagnostics show healthy KL/clip and normal action parity, downgrade the
cause to v10/reward/curriculum non-conversion. Even then, do not use loop112
as a continuation checkpoint.

## Structure / Research Synthesis

Key finding:
The next move should be a GRU/v10 wiring audit, not immediate BC/teacher
distillation and not another v40 maturation run.

Evidence:

- v40 had no partial memory signal: `0%` success and `0.0` mean gates at every
  milestone.
- Hard-eval actions were abnormally small compared with the frontier behavior:
  loop112 mean max command tilt was about `4.2 deg`, while loop107 frontier
  behavior had much larger command tilt and action deltas.
- This mismatch points to recurrent actor, v10 observation, checkpoint loading,
  hidden-state carry/reset, deterministic inference, or action scaling as the
  first area to audit.

Recommended next action:
Create a main-agent packet for:

```text
v41_gru_v10_recurrent_wiring_audit_and_zero_update_parity
```

The lane should perform read-only/small-test diagnostics before launching new
training. Feed-forward/v5 remains the control baseline. BC warm start or
teacher distillation should wait until the audit either fixes a wiring problem
or rules wiring out.

Risk / rollback:
If recurrent inference, v10 observation, checkpoint loading, hidden-state reset,
or action scaling is inconsistent, fix and re-run parity before any training.
If all audits pass but v10/GRU smoke still produces zero gates, reject v40
as-is and return to the verified pre-v40 frontier route with a new structural
packet.
