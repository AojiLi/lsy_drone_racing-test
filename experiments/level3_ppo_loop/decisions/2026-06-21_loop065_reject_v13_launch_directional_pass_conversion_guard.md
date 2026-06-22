# Loop065 Decision: Reject V13 Maturation, Launch Directional Pass Conversion Guard

## Decision

`change_reward_or_training_numbers`

Launch:

`v14_mlp_loop052_constant_lr_directional_pass_conversion_guard`

This is a bounded 20M reward/training-number screen. It starts from the
global-best loop052 checkpoint and keeps the v5 observation, 2x256 MLP, constant
learning rate, and nominal safety/control stack. It reduces raw gate pressure
relative to v13 and moves reward weight toward correct-side pass conversion and
wrong-side guarding.

## Hard Boundary

- Target hard eval remains `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not accept any result unless it is hard-evaluated on the unchanged Level3
  target track.

## Evidence

Loop065 tested:

- Proposal:
  `structural_v13_mlp_loop052_constant_lr_gate_acquisition_nominal_safety_20m`
- Initial checkpoint: loop052 final
- Observation layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Policy: 2x256 Tanh MLP
- Training: `learning_rate=5e-5`, `anneal_lr=False`
- Reward: stronger raw gate-acquisition numbers with nominal safety

Best loop065 hard eval:

- Checkpoint: final
- success_rate: 0.15
- mean_gates: 1.25
- mean successful time: 6.393s
- crash_rate: 0.85
- timeout_rate: 0.00

Global best remains loop052:

- success_rate: 0.20
- mean_gates: 1.40
- mean successful time: 6.975s
- crash_rate: 0.80

## Subagent Synthesis

Evaluator reviewer:

- Loop065 does not beat loop052.
- Final checkpoint is best inside loop065.
- It shows weak within-run improvement from 5M to final, so a 60M continuation
  could be considered only if other evidence supported conversion.

W&B/PPO reviewer:

- Constant learning rate worked and PPO update pressure is not dead.
- W&B race conversion does not support original v13 long training:
  `passed_gate_rate`, `finished_rate`, and `gate_plane_cross_rate` remain flat.
- If continuing the general area, make it a changed reward/training-number
  diagnostic rather than `continue_same_hypothesis`.

Structure/research reviewer:

- Reject the narrow v13 hypothesis.
- Do not reject v5 observation, 2x256 MLP, or constant learning rate.
- Next screen should test directional pass conversion and wrong-side guarding
  instead of further raw gate-acquisition scaling.

## Next Lane Contract

`v14_mlp_loop052_constant_lr_directional_pass_conversion_guard`

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
  - `gate_stage_coef=12`
  - `gate_axis_coef=18`
  - `gate_front_bonus=14`
  - `gate_bonus=150`
  - `gate_back_bonus=55`
  - `finish_bonus=220`
  - `wrong_side_penalty=14`
  - `time_penalty=0.0`
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

Promote the same hypothesis toward 60M if any milestone checkpoint beats
loop052's 0.20 success rate, materially exceeds 1.40 mean gates, or matches
0.20 success with `mean_gates > 1.40`, `crash_rate <= 0.80`, and improving W&B
pass/finish/plane-cross conversion.

Reject v14 if all milestone checkpoints stay at or below 0.15 success, remain
below 1.30 mean gates, or remain crash-heavy with flat W&B conversion. Also
reject if command tilt remains close to or worse than v13 final
`cmd_tilt_over_limit_frac=0.431`.
