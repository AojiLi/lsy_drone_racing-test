# loop035 Decoupled Frame-Clearance Synthesis

Date: 2026-06-20

## Purpose

Define one concrete next structural lane after loop035.

The target remains unchanged:

- hard eval on `config/level3_dr.toml`;
- success rate `>=0.60`;
- mean successful race time `<=7.0s`;
- no modification of Level3 track geometry or randomization.

## Current Frontier

Global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

## loop035 Result

Trial:

`level3_loop_035_structural_v5_frame_clearance_pass_conversion_reward_20m`

Best loop035 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_035_structural_v5_frame_clearance_pass_conversion_reward_20m/level3_loop_035_structural_v5_frame_clearance_pass_conversion_reward_20m_step_005000000.ckpt`
- Success rate: `0.00`
- Mean successful time: `null`
- Crash rate: `1.00`
- Mean gates: `0.85`

Milestone trend:

- 5M: `0.00` success, `1.00` crash, `0.85` mean gates
- 10M: `0.00` success, `1.00` crash, `0.20` mean gates
- 15M: `0.00` success, `1.00` crash, `0.10` mean gates
- final: `0.00` success, `1.00` crash, `0.10` mean gates

This does not qualify for 60M-90M maturation.

## Failure Diagnosis

loop035 tested `reward_structure=legacy_frame_clearance`.

That structure added:

- centered gate-plane crossing reward through `gate_plane_bonus`;
- continuous near-plane frame pressure through the same
  `missed_gate_penalty` used for discrete missed-gate events.

W&B evidence from loop035:

- `reward_components/missed_gate` tail mean: about `-50.78`
- `reward_components/gate_plane` tail mean: about `0.0005`
- `race/passed_gate_rate` tail mean: about `0.000122`
- `race/finished_rate`: `0.0`
- `race/gate_plane_dist` tail mean: about `1.00`
- `race/wrong_side_gate_rate` trended upward

Interpretation:

- The frame-pressure term dominated the reward scale.
- Centered gate-plane reward was too sparse to compensate.
- The policy did not learn centered crossing; it lost pass conversion.
- This is a reward-structure failure, not evidence against v5 observations,
  full 90-degree action authority, or the loop020 checkpoint as the base.

## Next Structural Lane

Name:

`v5_decoupled_frame_clearance_low_pressure_reward`

Proposal:

`structural_v5_decoupled_frame_clearance_low_pressure_reward_20m`

Mechanism:

- Keep loop020's v5 observation layout.
- Keep full `90deg` roll/pitch action authority.
- Keep PPO settings fixed.
- Keep loop020 completion-backloaded event rewards.
- Use a new training reward structure:
  `decoupled_frame_clearance`.
- Decouple dense frame pressure from discrete missed-gate penalty:
  - `missed_gate` penalizes only discrete missed plane crossings;
  - `gate_frame_pressure` is a separate logged component with a small
    coefficient.
- Restore obstacle penalty/margin to loop020-style values rather than loop035's
  stronger obstacle pressure.

This is not a track change. It only changes the training reward wrapper.

## Proposed Parameters

Start checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`

Training/eval:

- train config: `level3_dr.toml`
- eval config: `level3_dr.toml`
- train timesteps: `20_000_000`
- checkpoint interval: `5_000_000`
- W&B project: `ADR-PPO-Racing-Level3`

Changed for this lane:

- `reward_structure=decoupled_frame_clearance`
- `gate_plane_bonus=18.0`
- `missed_gate_penalty=8.0`
- `gate_frame_pressure_coef=1.5`
- `obstacle_coef=4.5`
- `obstacle_margin=0.3`

Keep fixed from loop020:

- observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- `action_rp_limit_deg=90.0`
- `action_lowpass_alpha=1.0`
- `learning_rate=0.0003`
- `gamma=0.99`
- `gae_lambda=0.95`
- `update_epochs=5`
- `num_minibatches=8`
- `ent_coef=0.02`
- `target_kl=0.03`
- `hidden_dim=256`
- `n_obs=2`
- `gate_stage_coef=9.0`
- `gate_axis_coef=22.0`
- `gate_bonus=180.0`
- `gate_front_bonus=22.0`
- `gate_back_bonus=95.0`
- `finish_bonus=300.0`
- `wrong_side_penalty=14.0`
- `crash_penalty=50.0`
- `time_penalty=0.005`
- `act_coef=0.012`
- `d_act_th_coef=0.055`
- `d_act_xy_coef=0.055`
- `cmd_tilt_coef=0.75`
- `rpy_coef=0.65`
- `tilt_limit_deg=42.0`
- `tilt_excess_coef=10.0`

## Promotion And Rollback

Promote or mature only if hard eval shows at least one:

- success rate above loop020: `>0.15`;
- mean gates above loop020: `>1.45`;
- same success as loop020 with materially lower crash or command saturation.

Reject if:

- best success remains `<=0.05`;
- mean gates stay below `1.10`;
- crash remains `>=0.95`;
- W&B `gate_frame_pressure` becomes dominant again;
- W&B frame/gate-plane signals move but hard-eval pass/finish stays flat.

## Required Follow-Up

After the train/evaluate chunk, immediately run the Level3 analyzer and the
three required post-run reviewers:

- evaluator metrics;
- W&B/PPO diagnostics;
- structure/research synthesis.

Do not launch a later chunk without a new main-agent decision packet.
