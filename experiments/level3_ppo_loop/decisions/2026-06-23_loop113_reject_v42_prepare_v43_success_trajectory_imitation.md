# Decision: Reject V42, Prepare V43 Success-Trajectory Imitation

Decision: `launch_named_structural_lane`

Resolved trial:
`level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m`

Analysis packet:
`experiments/level3_ppo_loop/analysis/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m_analysis.md`

Subagent synthesis:
`experiments/level3_ppo_loop/analysis/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m_subagent_reviews.md`

Approved next lane:

```text
v43_success_trajectory_imitation_warmstart_gru_v10
```

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue v42 as-is.
- Do not start future training from loop113 checkpoints.
- Keep deployment as:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is approved by this packet.

## Evidence

v42 failed its promotion gate:

- best checkpoint: `4M`;
- success: `0/100`;
- mean gates: `0.01`;
- crash rate: `54%`;
- timeout rate: `46%`;
- failures: `99%` at gate 0 and `1%` at gate 1;
- final checkpoint returned to `0.0` mean gates.

The corrected global best remains loop107 1M:

- success: `21%`;
- mean gates: `1.66`;
- crash rate: `79%`;
- mean successful time: `7.578s`.

Reviewer agreement:

- evaluator reviewer: reject v42 and do not continue from loop113 checkpoints;
- W&B/PPO reviewer: training-side gate signals did not transfer, and PPO was
  under-updating with very low KL and zero clip fraction;
- structure reviewer: v41 ruled out obvious GRU/v10 wiring bugs, so this is a
  start-distribution / skill-composition failure. The next lane should be
  success-trajectory imitation warm start, not reward-only tuning.

## Approved V43 Scope

`v43_success_trajectory_imitation_warmstart_gru_v10`

This is approved as the next structural direction, but not as an immediate PPO
training launch until the support preflight passes.

Required preflight:

1. Build or audit a success-trajectory dataset with v10 student observations
   and teacher action distributions from successful train-pool rollouts.
2. Implement or verify sequence-aware behavior-cloning warmstart support for
   `recurrent_actor_gru256`.
3. Save a GRU/v10 checkpoint with correct metadata and action envelope.
4. Verify load/save parity and nontrivial supervised action learning.
5. Hard-eval the BC checkpoint on unchanged `config/level3.toml` as a
   diagnostic.

If preflight passes, launch a bounded PPO fine-tune from the v43 BC checkpoint
with W&B logging and milestone hard eval. The teacher or imitation data may be
used only during training/pretraining; it is not part of inference.

## Not Approved

- Do not relaunch v42 with more steps.
- Do not continue from loop113 3M, 4M, final, or any loop113 checkpoint.
- Do not make a reward-only follow-up to v42.
- Do not add a planner, MPC, rule controller, shield, or fallback controller.
- Do not alter `config/level3.toml`.

## Promotion / Rejection Rule

Promote v43 if its BC checkpoint or first PPO screen shows:

- nonzero hard-eval success; or
- mean gates above `0.5`; or
- clear first-gate conversion beyond v42's `0.01` mean gates.

Reject or redesign v43 if imitation metrics improve but normal-start hard eval
remains `0%` success and below `0.5` mean gates.
