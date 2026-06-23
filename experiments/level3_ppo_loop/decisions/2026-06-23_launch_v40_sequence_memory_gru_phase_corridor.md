# Decision: Launch V40 Sequence-Memory GRU Phase-Corridor Screen

Decision: `launch_named_structural_lane`

Approved lane:

```text
v40_sequence_memory_gru_phase_corridor_from_scratch
```

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue v39b as the main route without new hard-eval evidence.
- Do not continue v37/v38 residual-GRU or teacher-retention routes as-is.
- Do not restore the rejected all-gates/v4 observation lane.

Deployment remains:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is approved by this packet.

## Evidence

The current frontier is a 19%-21% hard-eval plateau on
`validation_unseen` for unchanged `config/level3.toml`.

- loop101 / v33: 20% success, 1.69 mean gates, 80% crash.
- loop107 / v37: 21% success, 1.66 mean gates, 79% crash at 1M, then drifted.
- loop109 / v38: teacher retention was active but hard eval regressed to 18%.
- loop110 / v39: 21% success, 1.64 mean gates, 79% crash at 3M, then drifted.

The success seed set reshuffles rather than accumulates. This supports the
user's diagnosis that Level3 is likely bottlenecked by unstable sequence memory
and local strategy, not by another small reward-number change.

## Approved V40 Scope

`v40_sequence_memory_gru_phase_corridor_from_scratch`

- Train config:
  unchanged `config/level3.toml`.
- Hard eval config:
  unchanged `config/level3.toml`.
- Actor observation:
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`.
- Policy:
  `recurrent_actor_gru256`.
- Controller:
  end-to-end PPO Actor only.
- Start:
  from scratch.
- Training horizon:
  bounded 5M screen.
- Checkpoints:
  1M milestone interval.
- PPO recurrent sequence:
  `num_steps=128`, `recurrent_sequence_len=128`.
- Reward:
  keep the v39 gate-acquisition numbers fixed for this first memory screen.

## Promotion / Rejection Rule

Promote or mature only if hard eval shows one of:

- success `> 21%`;
- success around `25%-30%`;
- mean gates `> 1.75` with lower crash;
- a clearly broader success-seed set without losing the old frontier behavior.

Reject v40 as-is if it stays at or below the 21% success plateau, stays near
1.6 mean gates, or repeats late-checkpoint collapse.

If v40 shows partial memory signal but drifts, the next packet should implement
sequence-level success-trajectory pretraining or imitation. That is a separate
trainer feature, not part of this first screen.

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v40_sequence_memory_gru_phase_corridor_from_scratch \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_110_structural_v39_feedforward_gate_acquisition_reward_loop101_5m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-23_level3_sequence_memory_gru_phase_corridor_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_launch_v40_sequence_memory_gru_phase_corridor.md
```

If the dry-run is clean, launch the same command without `--dry-run`.

