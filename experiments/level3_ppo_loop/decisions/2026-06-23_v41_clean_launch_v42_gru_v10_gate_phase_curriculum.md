# Decision: V41 Clean, Launch V42 GRU/V10 Gate-Phase Curriculum

Decision: `launch_named_structural_lane`

Resolved diagnostic lane:

- audit:
  `v41_gru_v10_recurrent_wiring_audit_and_zero_update_parity`
- report:
  `experiments/level3_ppo_loop/parity/2026-06-23_v41_gru_v10_wiring_audit.md`
- source analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m_analysis.md`

Approved next lane:

```text
v42_gru_v10_gate_phase_reset_curriculum_from_scratch
```

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not continue v40 as-is.
- Do not start future training from loop112 checkpoints.
- Keep deployment as:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is approved by this packet.

## Evidence

loop112 / v40 failed to acquire any hard-eval gate progress:

- best checkpoint: 3M;
- success: `0/100`;
- mean gates: `0.0`;
- crash rate: `52%`;
- timeout rate: `48%`;
- all failures at gate 0.

v41 then audited the suspected implementation layer and passed all checks:

- v10 training/inference observation parity: max abs diff `1.19e-7`;
- action-scale parity: all diffs `0.0`;
- train/inference recurrent Actor parity: all diffs `0.0`;
- zero-update save/reload parity: all diffs `0.0`;
- hidden-state reset/carry parity: sequence-vs-step action diff `5.96e-8`;
- recurrent PPO gradient/update sanity: nonzero gradients for GRU, Actor head,
  `actor_logstd`, and Critic; one update moved deterministic action by `0.1399`.

This means v40 should be rejected as a learning-distribution failure, not as an
obvious GRU/v10 wiring bug.

## Approved V42 Scope

`v42_gru_v10_gate_phase_reset_curriculum_from_scratch`

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
  from scratch. Do not use loop112 checkpoints.
- Training horizon:
  bounded `10M` screen.
- Checkpoints:
  `1M` interval.
- Hard-eval milestones:
  `1M, 2M, 3M, 4M, 5M, 8M, 10M`.
- Curriculum:
  training-only gate-phase reset with probability `0.45`.
- Reward:
  keep v39 gate-acquisition numbers fixed for this screen.

## Promotion / Rejection Rule

Promote or mature if hard eval shows one of:

- nonzero success;
- mean gates above `0.5`;
- a clear passed-gate conversion signal relative to v40's `0.0` mean gates;
- crash reduction without simply replacing crashes with zero-gate timeouts.

Reject v42 as-is if all milestones remain `0` mean gates, if hard eval repeats
v40's low-action timeout behavior, or if W&B curriculum progress does not
convert into normal-start evaluator progress.

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v42_gru_v10_gate_phase_reset_curriculum_from_scratch \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_112_structural_v40_sequence_memory_gru_phase_corridor_5m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-23_level3_v42_gru_v10_gate_phase_curriculum_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_v41_clean_launch_v42_gru_v10_gate_phase_curriculum.md
```

If the dry-run is clean, launch the same command without `--dry-run`.
