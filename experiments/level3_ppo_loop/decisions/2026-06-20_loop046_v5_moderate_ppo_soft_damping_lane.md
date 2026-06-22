# Structural Lane Packet After loop046

Date: 2026-06-20

## Decision

Selected decision:

`launch_named_structural_lane`

Lane name:

`v5_loop020_moderate_ppo_soft_damping_30m`

## Why This Lane

loop046 rejected the v7 stability-retune path:

- Best loop046 hard eval: success `0.10`, mean gates `1.05`, crash `0.90`.
- 25M and final collapsed to `0.00` success and `1.00` crash.
- W&B showed no finish conversion, flat gate-plane conversion, near-zero
  clipfrac, and tail KL around `0.000004`.

The current global best is still loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure:
  `legacy_staged`
- Hard-eval success: `0.15`
- Mean gates: `1.45`
- Crash rate: `0.85`

Recent structural lanes did not beat this:

- v7 added explicit phase/progress but did not improve mean gates.
- v7 stability retune reduced command saturation but froze useful PPO movement.
- v5 PPO-pressure alone was too aggressive.
- v5 low-pass alone was too restrictive.
- gate-potential, direct-aperture, and soft-centerline reward structures did
  not produce stable pass conversion.

The next bounded test should therefore return to the strongest checkpoint and
test only a minimal training/controller structure combination:

- use loop020/v5 as the start;
- keep `legacy_staged` reward;
- keep the Level3 track unchanged;
- use moderate PPO pressure rather than low-learning-rate freezing;
- add only very mild action damping and moderate tilt/action penalties.

## Start Checkpoint

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

## Structure

- Train config: `level3_dr.toml`
- Hard eval config: `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Reward structure:
  `legacy_staged`
- Inference module:
  `ppo_level3_inference`
- Timesteps:
  `30_000_000`
- Checkpoint interval:
  `5_000_000`
- W&B project:
  `ADR-PPO-Racing-Level3`

## Parameter Changes From loop020

PPO/training pressure:

- `learning_rate`: `0.0003` -> `0.0002`
- `update_epochs`: `5` -> `6`
- `ent_coef`: `0.02` -> `0.01`
- `target_kl`: `0.03` -> `0.04`

Controller/action damping:

- `action_lowpass_alpha`: `1.0` -> `0.85`
- `action_rp_limit_deg`: keep `90.0`

Safety/smoothness:

- `act_coef`: `0.012` -> `0.014`
- `d_act_th_coef`: `0.055` -> `0.065`
- `d_act_xy_coef`: `0.055` -> `0.065`
- `cmd_tilt_coef`: `0.75` -> `0.90`
- `rpy_coef`: `0.65` -> `0.75`
- `tilt_limit_deg`: `42.0` -> `40.0`
- `tilt_excess_coef`: `10.0` -> `12.0`

Reward/event values stay at the loop020 family values:

- `reward_structure=legacy_staged`
- `gate_stage_coef=9`
- `gate_axis_coef=22`
- `gate_bonus=180`
- `gate_front_bonus=22`
- `gate_back_bonus=95`
- `finish_bonus=300`
- disabled channels remain `0`
- `wrong_side_penalty=14`
- `crash_penalty=50`
- `obstacle_coef=4.5`
- `obstacle_margin=0.3`
- `time_penalty=0.005`

These values must be passed explicitly because the loop script may otherwise
derive an automatic reward-number proposal from the latest failed trial.

## Hypothesis

loop020 has the best gate-progress frontier but later attempts either saturated
commands or froze policy movement. This lane tests whether moderate PPO update
pressure plus light action damping can preserve loop020's gate progress while
reducing destructive action spikes.

Expected useful signs:

- hard-eval success `>0.15`, or
- mean gates `>1.45`, or
- same `0.15` success with lower crash and no worse mean gates, or
- W&B gate-plane and passed-gate rates improve without rising command
  saturation.

## Rollback Criteria

Reject this lane if:

- all evaluated checkpoints stay `<=0.10` success;
- all evaluated checkpoints stay `<1.25` mean gates;
- 25M/final collapse to `0.00` success and `1.00` crash;
- W&B clipfrac remains `0` and KL remains near zero while evaluator metrics do
  not improve;
- command tilt over-limit rises materially above loop020 without hard-eval
  progress.

## Dry-Run Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --proposal-name v5_loop020_moderate_ppo_soft_damping_30m \
  --observation-layout level3_target_gate_nearest_gate_2obs_local_history_v5 \
  --train-timesteps 30000000 \
  --checkpoint-interval 5000000 \
  --initial-checkpoint lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_046_v7_10m_stability_retune_from_loop045_30m_analysis.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop046_hold_for_structural_lane_packet.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-20_loop046_v5_moderate_ppo_soft_damping_lane.md \
  --param learning_rate=0.0002 \
  --param update_epochs=6 \
  --param ent_coef=0.01 \
  --param target_kl=0.04 \
  --param action_rp_limit_deg=90 \
  --param action_lowpass_alpha=0.85 \
  --param reward_structure=legacy_staged \
  --param progress_coef=0.0 \
  --param gate_stage_coef=9 \
  --param gate_axis_coef=22 \
  --param near_gate_coef=0.0 \
  --param gate_bonus=180 \
  --param gate_front_bonus=22 \
  --param gate_plane_bonus=0.0 \
  --param gate_back_bonus=95 \
  --param finish_bonus=300 \
  --param missed_gate_penalty=0.0 \
  --param gate_frame_pressure_coef=0.0 \
  --param wrong_side_penalty=14 \
  --param crash_penalty=50 \
  --param obstacle_coef=4.5 \
  --param obstacle_margin=0.3 \
  --param obstacle_clearance_coef=0.0 \
  --param timeout_penalty=80 \
  --param time_penalty=0.005 \
  --param act_coef=0.014 \
  --param d_act_th_coef=0.065 \
  --param d_act_xy_coef=0.065 \
  --param cmd_tilt_coef=0.90 \
  --param rpy_coef=0.75 \
  --param tilt_limit_deg=40 \
  --param tilt_excess_coef=12
```

If the dry-run is clean, run the same command without `--dry-run`.

## Boundaries

- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- Do not modify `notebooks/train_level3_ppo.ipynb`.
- Do not treat W&B reward as acceptance; use it only for diagnosis.
