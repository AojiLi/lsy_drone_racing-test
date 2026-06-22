# Level3 Decision: V5 Gate-Acquisition Repair After Loop 015

Date: 2026-06-19

## Trial

- Trial id: `level3_loop_015_structural_v5_localobs_remote_reward_30m`
- Analysis report:
  `experiments/level3_ppo_loop/analysis/level3_loop_015_structural_v5_localobs_remote_reward_30m_analysis.md`
- Analysis JSON:
  `experiments/level3_ppo_loop/analysis/level3_loop_015_structural_v5_localobs_remote_reward_30m_analysis.json`
- W&B run:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_015_structural_v5_localobs_remote_reward_30m`
- Best v5 checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_015_structural_v5_localobs_remote_reward_30m/level3_loop_015_structural_v5_localobs_remote_reward_30m_step_015000000.ckpt`
- Hard-eval success rate: `0.00`
- Mean successful time: none
- Crash rate: `0.95`
- Mean gates: `0.40`
- Target met: no

## Subagent Findings

- `evaluator_metrics`: The best checkpoint is the 15M v5 checkpoint with
  `0%` success and `0.40` mean gates. This is worse than the standing global
  best, which has `5%` success and `0.95` mean gates. The branch does not earn
  unchanged 60M-90M maturation.
- `wandb_ppo_diagnostics`: PPO appears stable. Reward and some gate-shaping
  signals improved, but they did not convert into hard-eval success. KL and
  clipfrac are low late in training; the failure is behavioral conversion, not
  optimizer blow-up.
- `structure_research_synthesis`: External stateirving evidence still supports
  v5 over the rejected all-gates/v4 lane, but the local remote-recipe 30M screen
  is under-driven for gate acquisition. Preserve v5 for one repair screen, but
  do not continue the same recipe unchanged.

## Main-Agent Decision

Selected decision: `change_reward_or_training_numbers`

This packet does not launch a new structural lane. It keeps the approved v5
observation layout and changes reward/training numbers inside that lane.

## Rationale

- Local evaluator evidence: v5 remote recipe regressed versus the standing
  global best: `success_rate -0.05`, `mean_gates -0.55`, no successful run.
- W&B evidence: `train/total_reward` improved, `race/gate_stage` increased, and
  value diagnostics improved, but `race/finished_rate` stayed `0` and
  `race/passed_gate_rate` remained effectively flat.
- PPO/training evidence: no KL, clip, or value-loss instability justifies an
  immediate optimizer rewrite. Keep PPO hyperparameters fixed for this repair
  screen.
- Structural evidence: v5 is still the best source-backed observation direction,
  but unchanged maturation would spend long-run budget on a branch that has not
  met the Level2 step-curve promise threshold.
- External evidence: the stateirving packet supports v5 local-obstacle
  observation, but remote checkpoints only become useful after much longer
  training and still remain below the target. The next local step should test
  stronger gate-acquisition pressure before any long continuation.

## Approved Next Experiment

Name: `v5_gate_acquisition_repair_30m`

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_015_structural_v5_localobs_remote_reward_30m/level3_loop_015_structural_v5_localobs_remote_reward_30m_step_015000000.ckpt
```

Observation layout:

```text
level3_target_gate_nearest_gate_2obs_local_history_v5
```

Approved parameter changes versus the v5 remote recipe. The gate-acquisition
numbers are the primary change; the loop's automatic high-crash base proposal
also raises safety/smoothness pressure before the explicit gate overrides are
applied.

```text
gate_stage_coef=13.0
gate_axis_coef=24.0
gate_front_bonus=5.0
gate_bonus=200.0
gate_back_bonus=35.0
finish_bonus=175.0
crash_penalty=62.5
obstacle_coef=5.75
act_coef=0.0345
d_act_th_coef=0.112
d_act_xy_coef=0.112
cmd_tilt_coef=1.12
rpy_coef=1.1
tilt_limit_deg=38.0
time_penalty=0.02
```

Keep PPO hyperparameters unchanged for this screen:

```text
learning_rate=3e-4
ent_coef=0.02
target_kl=0.03
hidden_dim=256
n_obs=2
```

## Next Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --proposal-name v5_gate_acquisition_repair_30m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_015_structural_v5_localobs_remote_reward_30m/level3_loop_015_structural_v5_localobs_remote_reward_30m_step_015000000.ckpt \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_015_structural_v5_localobs_remote_reward_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-19_stateirving_level3_remote_reference.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-19_v5_gate_acquisition_repair_after_loop015.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Promotion And Rollback

- Promote this v5 repair branch toward 60M only if hard eval reaches non-zero
  success or at least `0.75` mean gates.
- If it remains `0%` success and below `0.75` mean gates, stop spending on v5
  reward-number tweaks and require a new named structural lane or research
  packet.
- Do not modify Level3 track geometry or randomization. Final acceptance remains
  hard eval on `config/level3_dr.toml`.
