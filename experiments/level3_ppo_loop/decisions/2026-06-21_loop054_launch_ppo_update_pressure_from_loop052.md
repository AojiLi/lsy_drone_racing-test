# Main-Agent Decision After loop054

Date: 2026-06-21

## Trial

- Trial:
  `level3_loop_054_v5_loop052_mild_gate_pressure_nominal_safety_20m`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_054_v5_loop052_mild_gate_pressure_nominal_safety_20m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_054_v5_loop052_mild_gate_pressure_nominal_safety_20m`

Best loop054 checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_054_v5_loop052_mild_gate_pressure_nominal_safety_20m/level3_loop_054_v5_loop052_mild_gate_pressure_nominal_safety_20m_step_005000000.ckpt`

Hard-eval metrics:

- Success rate: `0.15`
- Mean successful time: `6.14s`
- Crash rate: `0.85`
- Timeout rate: `0.00`
- Mean gates: `1.20`

Global best remains loop052:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

with success `0.20`, mean successful time `6.975s`, crash `0.80`,
and mean gates `1.40`.

## Subagent Findings

- `evaluator_metrics` recommended `launch_named_structural_lane`.
  loop054 rejected the mild gate-pressure reward tweak on hard eval.
- `wandb_ppo_diagnostics` recommended `launch_named_structural_lane`.
  It found reward improved but race conversion stayed flat, while KL and
  clipfrac remained very low. This looks like under-updating, not a
  reward-only issue.
- `structure_research_synthesis` recommended
  `launch_named_structural_lane`.
  It found repeated reward changes from loop052 are now sufficiently falsified
  and recommended a named PPO update-pressure lane from loop052 final.

## Main-Agent Decision

Selected decision:

`launch_named_structural_lane`

Launch a narrow training-structure lane from loop052 final. Keep the Level3
track, v5 observation, controller, reward structure, and loop052 nominal reward
numbers fixed. Only increase PPO update pressure.

## Rationale

loop052 is the only positive breakthrough so far. loop053 and loop054 both
started from that neighborhood but did not convert:

- loop053 same-reward maturation kept success at `0.20` but dropped mean gates
  to `1.15`;
- loop054 reward-number probing regressed to `0.15` success and `0.85` crash;
- W&B race conversion stayed flat across the failed continuation/tuning runs;
- PPO diagnostics repeatedly showed low KL and near-zero clipfrac.

The next falsifiable question is whether the loop052 policy needs stronger
optimizer update pressure rather than another reward-scale change.

This is a structural/training lane and must be evaluated as such. It is not a
reward-only run.

## Approved Next Experiment

Name:

`v5_loop052_nominal_reward_ppo_update_pressure_20m`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Research packet:

`experiments/level3_ppo_loop/research/2026-06-21_remote_nominal_reward_dr_lane_addendum.md`

Settings:

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure: `legacy_staged`
- Controller:
  `action_rp_limit_deg=90`, `action_lowpass_alpha=1.0`
- Reward numbers:
  keep loop052 nominal values unchanged.
- Train timesteps: `20_000_000`
- Checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`

Training-structure changes versus loop052:

- `learning_rate: 5e-5 -> 8e-5`
- `update_epochs: 5 -> 6`

Keep the rest of the PPO/training structure unchanged:

- `gamma = 0.99`
- `gae_lambda = 0.95`
- `num_minibatches = 8`
- `ent_coef = 0.02`
- `target_kl = 0.03`
- `hidden_dim = 256`
- `n_obs = 2`

## Required Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --override-state-hold \
  --proposal-name v5_loop052_nominal_reward_ppo_update_pressure_20m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 20000000 \
  --checkpoint-interval 5000000 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_054_v5_loop052_mild_gate_pressure_nominal_safety_20m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-21_remote_nominal_reward_dr_lane_addendum.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop054_launch_ppo_update_pressure_from_loop052.md \
  --param learning_rate=0.00008 \
  --param gamma=0.99 \
  --param gae_lambda=0.95 \
  --param update_epochs=6 \
  --param num_minibatches=8 \
  --param ent_coef=0.02 \
  --param target_kl=0.03 \
  --param hidden_dim=256 \
  --param n_obs=2 \
  --param action_rp_limit_deg=90.0 \
  --param action_lowpass_alpha=1.0 \
  --param reward_structure=legacy_staged \
  --param progress_coef=0.0 \
  --param gate_stage_coef=10.0 \
  --param gate_axis_coef=12.0 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=90.0 \
  --param gate_front_bonus=0.0 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=12.0 \
  --param finish_bonus=160.0 \
  --param missed_gate_penalty=0.0 \
  --param gate_frame_pressure_coef=0.0 \
  --param wrong_side_penalty=8.0 \
  --param crash_penalty=100.0 \
  --param obstacle_coef=8.0 \
  --param obstacle_margin=0.40 \
  --param obstacle_clearance_coef=6.0 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.03 \
  --param act_coef=0.03 \
  --param d_act_th_coef=0.10 \
  --param d_act_xy_coef=0.10 \
  --param cmd_tilt_coef=1.0 \
  --param rpy_coef=1.0 \
  --param tilt_limit_deg=40.0 \
  --param tilt_excess_coef=15.0
```

If dry-run passes, run the same command without `--dry-run`.

## Promotion And Rollback

Promote if hard eval on `config/level3_dr.toml` shows:

- success rate `> 0.20`; or
- mean gates `> 1.45`; or
- crash rate `< 0.80`; or
- success `0.20` with mean gates at least `1.40` and W&B gate/finish
  conversion improving.

Reject or change lane if:

- best success falls to `<= 0.15`;
- mean gates stay below `1.20`;
- crash rises to `>= 0.85`;
- W&B update activity rises but `passed_gate_rate`, `finished_rate`, and
  `gate_plane_cross_rate` remain flat while evaluator progress regresses.

After the chunk, immediately run:

```bash
pixi run -e gpu python scripts/analyze_level3_ppo_trial.py \
  --wandb-entity aojili77-technical-university-of-munich \
  --require-wandb-online
```

Then repeat the three-review decision gate before any further training.
