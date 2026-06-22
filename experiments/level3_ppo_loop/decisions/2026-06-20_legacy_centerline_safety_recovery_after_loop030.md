# Main-Agent Decision: Legacy Centerline Safety Recovery After loop030

Date: 2026-06-20

## Decision

`change_reward_or_training_numbers`

Launch one bounded 30M screen:

`v5_legacy_centerline_safety_recovery_from_loop020_25m_30m`

## Evidence

- Hard eval remains on immutable `config/level3_dr.toml`.
- Global best remains loop020 25M:
  - success rate: `0.15`
  - mean successful time: `6.366666666666667`
  - crash rate: `0.85`
  - mean gates: `1.45`
- loop030 did not promote:
  - best success rate: `0.05`
  - best mean gates: `1.1`
  - best crash rate: `0.95`
  - later checkpoints collapsed to `0.0` success
- loop029 and loop030 together reject continuing the current gate-potential
  family without a deeper reward-structure change.

## Source Packet

Use:

`experiments/level3_ppo_loop/research/2026-06-20_legacy_centerline_safety_recovery_after_gate_potential.md`

Summary:

- External drone-racing RL work supports projected gate/centerline progress and
  explicit safety pressure as practical dense rewards.
- Local code confirms front/back/pass event rewards are active in
  `legacy_staged` but zeroed in `gate_potential`.
- Local trials show the current best checkpoint came from the
  `legacy_staged` family, while gate-potential lanes failed to convert W&B
  proxy progress into stable hard-eval passage.

## Next Experiment

Start checkpoint:

```text
lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt
```

Keep:

- observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- reward structure:
  `legacy_staged`
- PPO/network settings unchanged
- action authority:
  `action_rp_limit_deg=90.0`, `action_lowpass_alpha=1.0`
- train horizon:
  `30M` with `5M` checkpoint interval

Reward/training numbers:

- `gate_stage_coef=11.0`
- `gate_axis_coef=28.0`
- `gate_front_bonus=12.0`
- `gate_bonus=190.0`
- `gate_back_bonus=45.0`
- `finish_bonus=240.0`
- `wrong_side_penalty=12.0`
- `crash_penalty=70.0`
- `obstacle_coef=5.5`
- `time_penalty=0.01`
- `act_coef=0.018`
- `d_act_th_coef=0.08`
- `d_act_xy_coef=0.08`
- `cmd_tilt_coef=1.05`
- `rpy_coef=0.9`
- `tilt_limit_deg=40.0`
- `tilt_excess_coef=16.0`

## Next Command

Dry-run first:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --proposal-name v5_legacy_centerline_safety_recovery_from_loop020_25m_30m \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_030_v5_gate_potential_pass_conversion_from_loop028_25m_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-20_legacy_centerline_safety_recovery_after_gate_potential.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_legacy_centerline_safety_recovery_after_loop030.md \
  --param learning_rate=0.0003 \
  --param gamma=0.99 \
  --param gae_lambda=0.95 \
  --param update_epochs=5 \
  --param num_minibatches=8 \
  --param ent_coef=0.02 \
  --param target_kl=0.03 \
  --param hidden_dim=256 \
  --param n_obs=2 \
  --param action_rp_limit_deg=90.0 \
  --param action_lowpass_alpha=1.0 \
  --param reward_structure=legacy_staged \
  --param progress_coef=0.0 \
  --param gate_stage_coef=11.0 \
  --param gate_axis_coef=28.0 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=190.0 \
  --param gate_front_bonus=12.0 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=45.0 \
  --param finish_bonus=240.0 \
  --param missed_gate_penalty=0.0 \
  --param wrong_side_penalty=12.0 \
  --param crash_penalty=70.0 \
  --param obstacle_coef=5.5 \
  --param obstacle_margin=0.3 \
  --param obstacle_clearance_coef=0.0 \
  --param timeout_penalty=80.0 \
  --param time_penalty=0.01 \
  --param act_coef=0.018 \
  --param d_act_th_coef=0.08 \
  --param d_act_xy_coef=0.08 \
  --param cmd_tilt_coef=1.05 \
  --param rpy_coef=0.9 \
  --param tilt_limit_deg=40.0 \
  --param tilt_excess_coef=16.0
```

If dry-run passes, launch the same command without `--dry-run`.

## Promotion And Rollback

- Promote or mature only if the run beats loop020's `0.15` success, loop020's
  `1.45` mean gates, or ties success while materially reducing crash/tilt.
- Reject if best success is `<=0.05`, mean gates remain below `1.15`, or
  command tilt over-limit exceeds `0.65` without evaluator improvement.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
