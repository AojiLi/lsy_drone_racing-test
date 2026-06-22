# loop034 Frame-Clearance Pass-Conversion Synthesis

Date: 2026-06-20

## Purpose

Define one concrete next structural lane after loop034 before any further
training.

The target remains:

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
- Command tilt over-limit fraction: `0.5800860395510893`

## Recent Negative Evidence

Loop027 tested the analyzer's gate-acquisition reward-number direction:

- Success rate: `0.05`
- Mean gates: `0.80`
- Crash rate: `0.95`
- Command tilt over-limit fraction: `0.8259534779373124`

Loop033 tested higher PPO update pressure and lower entropy:

- Success rate: `0.05`
- Mean gates: `1.10`
- Crash rate: `0.95`
- Command tilt over-limit fraction: `0.508806638074582`

Loop034 tested a milder checkpointed action low-pass:

- Success rate: `0.05`
- Mean gates: `0.90`
- Crash rate: `0.95`
- Command tilt over-limit fraction: `0.44113195808597394`

Conclusion:

- reward-number rebalance alone failed;
- PPO pressure/entropy alone failed;
- controller smoothing alone failed;
- smoother control can reduce command saturation while still reducing gate
  conversion.

## Crash-Taxonomy Evidence

loop020 40-seed hard-eval crash taxonomy:

- Successes: `3/40`
- Crash rate: `0.925`
- Crashes by target gate: gate 0 `16`, gate 1 `14`, gate 2 `6`, gate 3 `1`
- Main likely objects: obstacle 1 `7`, obstacle 0 `6`, gate 0 right `5`,
  gate 1 left `3`, gate 1 right `2`, gate 2 right `2`, obstacle 2 `2`,
  obstacle 3 `2`

loop034 40-seed hard-eval crash taxonomy:

- Successes: `2/40`
- Crash rate: `0.95`
- Crashes by target gate: gate 0 `15`, gate 1 `15`, gate 2 `7`, gate 3 `1`
- Main likely objects: obstacle 0 `9`, obstacle 1 `6`, gate 1 left `5`,
  gate 2 top `5`, gate 0 left `3`, obstacle 2 `3`

Interpretation:

- failures are concentrated around the first two gates and nearby
  obstacles/frame parts;
- smoother commands do not solve the path geometry problem;
- the next mechanism should teach centered gate-plane crossing and discourage
  near-plane frame approaches before collision.

## Next Structural Lane

Name:

`v5_frame_clearance_pass_conversion_reward`

Proposal:

`structural_v5_frame_clearance_pass_conversion_reward_20m`

Mechanism:

- Keep loop020's v5 observation, full action authority, PPO settings, and
  completion-backloaded event rewards.
- Add a new training reward structure:
  `legacy_frame_clearance`.
- `legacy_frame_clearance` keeps the legacy staged reward components but
  changes two currently inactive/weak terms:
  - `gate_plane`: reward centered crossing of the current gate plane when
    the drone crosses the plane inside the staged gate radius;
  - `missed_gate`: add a continuous near-plane frame-clearance penalty when
    the drone approaches the gate plane outside the safe center corridor.
- Slightly strengthen obstacle margin/penalty because both loop020 and loop034
  crash frequently on obstacle 0/1/2 near early gates.

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

Changed for this lane:

- `reward_structure=legacy_frame_clearance`
- `gate_plane_bonus=35.0`
- `missed_gate_penalty=18.0`
- `obstacle_coef=6.0`
- `obstacle_margin=0.35`

## Promotion And Rollback

Promote or mature only if a hard-eval checkpoint shows at least one:

- success rate above loop020: `>0.15`;
- mean gates above loop020: `>1.45`;
- same success as loop020 with materially lower crash or command saturation.

Secondary screen:

- must beat loop034 on both success and mean gates;
- must not collapse to `0%` final success with lower mean gates.

Reject if:

- best success remains `<=0.05`;
- mean gates stay below `1.10`;
- crash remains `>=0.95`;
- W&B `gate_plane`/`missed_gate` terms move but `passed_gate_rate` and
  `finished_rate` stay flat;
- the policy avoids the gate corridor instead of crossing it.

## Required Follow-Up

After the train/evaluate chunk, immediately run the Level3 analyzer and the
three required post-run reviewers:

- evaluator metrics;
- W&B/PPO diagnostics;
- structure/research synthesis.

Do not launch a later chunk without a new main-agent decision packet.
