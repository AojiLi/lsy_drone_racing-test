# Decision: Launch V43 PPO Fine-Tune From Success-Trajectory BC Warmstart

Decision: `launch_named_structural_lane`

Approved next lane:

```text
v43_success_trajectory_imitation_warmstart_gru_v10
```

Preflight packet:

`experiments/level3_ppo_loop/parity/2026-06-23_v43_success_trajectory_bc_warmstart_preflight.md`

Parent post-run decision:

`experiments/level3_ppo_loop/decisions/2026-06-23_loop113_reject_v42_prepare_v43_success_trajectory_imitation.md`

Research packet:

`experiments/level3_ppo_loop/research/2026-06-23_level3_v43_success_trajectory_imitation_warmstart_plan.md`

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

The teacher and BC dataset are allowed only as training/pretraining support.
They are not part of inference.

## Evidence

loop113/v42 failed to acquire normal-start gate progress:

- best success: 0%
- best mean gates: 0.01
- best crash rate: 54%
- best timeout rate: 46%

v43 BC preflight passed its supervised-learning check:

- dataset: 8 successful train-pool trajectories from seeds 2001-2049;
- excluded seed ranges: `1-20,101-200,1001-1200`;
- student observation layout:
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`;
- policy arch: `recurrent_actor_gru256`;
- teacher action MSE improved from 0.2659 to 0.0015;
- teacher agreement improved from 0.2694 to 0.9911.

BC-only hard eval on unchanged `config/level3.toml`,
`validation_unseen_101_200`:

- success: 0/100;
- mean gates: 0.15;
- crash rate: 99%;
- timeout rate: 1%;
- failures by target gate: gate0 88, gate1 10, gate2 2, gate3 0.

The BC checkpoint is not a controller we can accept, but it does show
normal-start first-gate signal above the v40/v42 zero-gate failure mode.

## Approved V43 PPO Screen

Run exactly one bounded train/evaluate chunk:

- structural hypothesis:
  `v43_success_trajectory_imitation_warmstart_gru_v10`
- initial checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_v43_success_trajectory_bc_warmstart/level3_v43_success_trajectory_bc_warmstart.ckpt`
- policy arch: `recurrent_actor_gru256`
- observation layout:
  `level3_gate_corridor_aperture_margin_2obs_local_history_v10`
- training config: `config/level3.toml`
- hard eval config: `config/level3.toml`
- train timesteps: 10M
- checkpoint interval: 1M
- hard-eval milestones: 1M, 2M, 3M, 4M, 5M, 8M, 10M/final
- reward numbers: keep v39 gate-acquisition scale fixed for this screen.

Use W&B online logging and the standard post-run analyzer. After the chunk,
spawn exactly three read-only reviewers:

1. evaluator metrics;
2. W&B/PPO diagnostics;
3. structure/research synthesis.

The main agent must write a new decision packet before any next training
chunk.

## Promotion / Rejection Rule

Promote or mature v43 if a milestone checkpoint shows at least one of:

- nonzero hard-eval success;
- mean gates above 0.5;
- materially lower crash than the 79% plateau;
- first-gate conversion that continues beyond the BC-only diagnostic.

Reject or redesign v43 if PPO erases the BC first-gate signal, remains below
0.5 mean gates, or improves W&B training curves without validation_unseen gate
progress.

## Suggested Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --structural-hypothesis v43_success_trajectory_imitation_warmstart_gru_v10 \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-23_level3_v43_success_trajectory_imitation_warmstart_plan.md \
  --research-packet experiments/level3_ppo_loop/parity/2026-06-23_v43_success_trajectory_bc_warmstart_preflight.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_loop113_reject_v42_prepare_v43_success_trajectory_imitation.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-23_v43_bc_preflight_launch_v43_ppo_finetune.md
```
