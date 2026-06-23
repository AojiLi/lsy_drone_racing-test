# Decision: Reject V40 and Launch V41 GRU/V10 Wiring Audit

Decision: `launch_named_structural_lane`

Pending gate resolved by this packet:

- trial:
  `level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m`
- analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m_analysis.md`
- subagent synthesis:
  `experiments/level3_ppo_loop/analysis/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m_subagent_reviews.md`

Approved next lane:

```text
v41_gru_v10_recurrent_wiring_audit_and_zero_update_parity
```

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue v40 as-is.
- Do not start future training from loop112 checkpoints.
- Do not run a long GRU/v10 training continuation until v41 diagnostics pass.
- Keep deployment as:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is approved by this packet.

## Evidence

Best loop112 / v40 checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m_step_003000000.ckpt`
- success: `0/100`
- mean gates: `0.0`
- crash rate: `52%`
- timeout rate: `48%`
- mean successful time: none
- failures by target gate: `{"0": 100}`

Milestone summary:

| Checkpoint | Success | Mean Gates | Crash | Timeout |
| --- | ---: | ---: | ---: | ---: |
| 1M | 0% | 0.0 | 64% | 36% |
| 2M | 0% | 0.0 | 57% | 43% |
| 3M | 0% | 0.0 | 52% | 48% |
| 4M | 0% | 0.0 | 54% | 46% |
| final | 0% | 0.0 | 53% | 47% |

Reference frontier:

- loop101 / v33: `20%` success, `1.69` mean gates, `80%` crash,
  `6.873s` mean successful time.
- loop107 / v37: `21%` success, `1.66` mean gates, `79%` crash,
  `7.578s` mean successful time at 1M.
- loop110 / v39: `21%` success, `1.64` mean gates, `79%` crash,
  `6.756s` mean successful time at 3M.

v40 therefore did not merely miss the 21% plateau. It failed to acquire gate 0
at every evaluated milestone. The lower crash rate is not progress because it
came with high timeout and zero gate progress.

W&B/PPO diagnostics also argue against maturation:

- `approx_kl=0.0`
- `clipfrac=0.0`
- `policy_loss=-7e-06`
- `entropy=0.708`
- `explained_variance=0.001243`
- `race/passed_gate_rate=3.1e-05`
- `race/finished_rate=0.0`
- `race/gate_stage=0.004089`

These signals are consistent with ineffective actor learning or a recurrent /
observation / action-scale wiring issue, not with a branch that simply needs
more steps.

## Reviewer Synthesis

- Evaluator reviewer: reject v40 as-is; no checkpoint is promising enough to
  mature.
- W&B/PPO reviewer: do not tune reward numbers or run a long continuation until
  recurrent PPO/action wiring sanity checks pass.
- Structure reviewer: launch a GRU/v10 wiring audit first. BC warm start or
  teacher distillation should wait because v40 showed no partial memory signal.

## Approved V41 Scope

`v41_gru_v10_recurrent_wiring_audit_and_zero_update_parity`

This is a diagnostic structural lane, not a long training lane.

Required checks:

1. Recurrent Actor zero-update parity:
   loading a v40 checkpoint and saving/reloading it without updates must
   preserve deterministic actions and values on fixed v10 observations.
2. Train/eval action-scale parity:
   deterministic inference through `ppo_level3_inference.py` must match the
   trainer Agent for the same checkpoint, observation tensor, recurrent hidden
   state, and done mask.
3. Hidden-state reset/carry parity:
   episode reset must clear recurrent state; within-episode sequential calls
   must carry state and change only through the GRU path.
4. v10 observation sanity:
   fixed seeds must produce finite v10 observations with expected dimensions,
   nonzero phase/corridor/aperture features, bounded magnitudes, and correct
   reset behavior.
5. PPO recurrent update sanity:
   on a tiny controlled batch or smoke rollout, recurrent Actor parameters and
   `actor_logstd` must receive nonzero gradients, and a small update must move
   action means.
6. Hard-eval smoke:
   if code changes are needed, run a short deterministic smoke eval on
   unchanged `config/level3.toml` to confirm inference no longer collapses to
   near-static low-tilt commands before launching a new long training branch.

## Promotion / Rejection Rule

Promote to a new train/evaluate lane only if v41 diagnostics pass or identify
and fix a concrete recurrent/v10/action-scale bug.

If v41 finds a bug:

- fix it in code;
- add regression tests;
- write a new decision packet for the corrected GRU/v10 training lane;
- do not use loop112 checkpoints as the start.

If v41 finds no wiring bug:

- reject v40 as-is;
- return to the verified pre-v40 frontier as the control baseline;
- create a new explicit structural packet before trying BC warm start, teacher
  distillation, altered observation layout, altered PPO update pressure, or a
  new curriculum.

## Next Goal

Use this packet for the next Codex-supervised diagnostic goal:

```text
Use $level3-ppo-loop to run the v41 GRU/v10 recurrent wiring audit for
level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m. Do not
launch new training. Read the loop112 analysis and subagent reviews, then
implement and run deterministic checks for recurrent Actor zero-update parity,
train/eval action-scale parity, hidden-state reset/carry parity, v10
observation sanity, and recurrent PPO gradient/update sanity. Keep
config/level3.toml unchanged. If a bug is found, fix it, add regression tests,
write a v41 audit report under experiments/level3_ppo_loop/parity/ or
analysis/, and commit + push. If all audits pass, write a decision packet
rejecting v40 as-is and proposing the next named structural lane without
launching training.
```
