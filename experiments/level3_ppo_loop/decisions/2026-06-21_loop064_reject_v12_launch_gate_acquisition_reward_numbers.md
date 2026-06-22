# Loop064 Decision: Reject V12 Maturation, Launch Gate-Acquisition Reward Numbers

## Decision

`change_reward_or_training_numbers`

Launch:

`v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety`

This is a bounded 20M reward/training-number screen. It starts from the
global-best loop052 checkpoint and keeps the v5 observation, 2x256 MLP, constant
learning rate, and nominal safety/control stack. It changes only the gate
acquisition and completion reward numbers listed below.

## Hard Boundary

- Target hard eval remains `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not accept any result unless it is hard-evaluated on the unchanged Level3
  target track.

## Evidence

Loop064 tested:

- Proposal: `structural_v12_mlp_loop052_constant_lr_nominal_reward_20m`
- Initial checkpoint: loop052 final
- Observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Policy: 2x256 Tanh MLP
- Training-number change: `anneal_lr=False`
- Reward numbers: loop052 nominal

Best loop064 hard eval:

- Checkpoint: 10M
- success_rate: 0.15
- mean_gates: 1.15
- mean successful time: 6.46s
- crash_rate: 0.85
- timeout_rate: 0.00

The 5M checkpoint reached `mean_gates=1.40`, but success stayed at 0.15 and
later checkpoints regressed to 0.05-0.10 success with `mean_gates=1.05`.

Global best remains loop052:

- success_rate: 0.20
- mean_gates: 1.40
- mean successful time: 6.975s
- crash_rate: 0.80

## Subagent Synthesis

Evaluator reviewer:

- Reject v12 maturation.
- Loop064 does not beat loop052 on success, mean gates, or crash.
- The 15M/final regression argues against continuing the same branch to
  60M/90M.

W&B/PPO reviewer:

- Constant learning rate did work: W&B shows `charts/learning_rate=5e-05`.
- PPO update pressure exists: KL and clip fraction are nonzero.
- The issue is conversion, not a dead optimizer: passed-gate and finish rates
  remain flat and hard-eval progress does not improve.

Structure/research reviewer:

- Reject only the narrow v12 hypothesis.
- Do not reject v5 observation, 2x256 MLP, or constant learning rate globally.
- Next best move is a bounded reward/training-number screen focused on gate
  acquisition rather than a new architecture lane.

## Next Lane Contract

`v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety`

- Initial checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`
- Observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Actor/Critic:
  existing 2x256 Tanh MLP
- Training:
  `learning_rate=5e-5`, `anneal_lr=False`
- Reward structure:
  `legacy_staged`
- Changed reward numbers:
  - `gate_stage_coef=13`
  - `gate_axis_coef=24`
  - `gate_front_bonus=5`
  - `gate_bonus=200`
  - `gate_back_bonus=35`
  - `finish_bonus=175`
  - `time_penalty=0.02`
- Keep nominal loop052 safety/control numbers:
  `crash_penalty=100`, `obstacle_coef=8`, `obstacle_margin=0.40`,
  `obstacle_clearance_coef=6`, `act_coef=0.03`, `d_act_th_coef=0.10`,
  `d_act_xy_coef=0.10`, `cmd_tilt_coef=1.0`, `rpy_coef=1.0`,
  `tilt_limit_deg=40`, `tilt_excess_coef=15`.
- Training horizon:
  20M screening with 5M checkpoint interval.
- Hard eval:
  unchanged `config/level3_dr.toml`.

## Promotion Rule

Promote the same hypothesis toward 60M/90M if any milestone checkpoint beats
loop052's 0.20 success rate, materially exceeds 1.40 mean gates, or matches
0.20 success while improving gate/finish conversion with crash no worse than
0.80.

Reject v13 if all milestone checkpoints stay at or below 0.15 success, do not
exceed 1.20 mean gates, or remain crash-heavy with flat W&B pass/finish
conversion.
