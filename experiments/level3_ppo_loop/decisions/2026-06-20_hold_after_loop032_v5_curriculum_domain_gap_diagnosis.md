# Main-Agent Decision After loop032

Date: 2026-06-20

## Decision

`hold_for_more_analysis`

Do not launch another train/evaluate chunk yet.

## Scope

- Keep final hard evaluation on `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization in `config/level3_dr.toml`.
- Do not continue
  `level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m`
  unchanged.
- Do not start another no-wrapper curriculum chunk until the command-saturation
  and train/eval transfer failure is diagnosed.

## Evidence

Analyzed trial:

- Trial:
  `level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m`
- Train config:
  `level3_dr_stage2_no_train_wrappers.toml`
- Hard eval config:
  `level3_dr.toml`
- Observation layout:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Initial checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_analysis.md`
- W&B:
  `https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m`

Best loop032 checkpoint:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_step_010000000.ckpt`
- Success rate: `0.0`
- Mean successful time: `null`
- Crash rate: `1.0`
- Mean gates: `0.8`
- Command tilt over-limit fraction: `0.7672794535902253`

All evaluated loop032 checkpoints had:

- success rate: `0.0`
- crash rate: `1.0`

Current global best remains loop020:

- Checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: `0.15`
- Mean successful time: `6.366666666666667s`
- Crash rate: `0.85`
- Mean gates: `1.45`

## Reviewer Synthesis

Evaluator metrics:

- Reject continuing loop032 unchanged.
- The branch regressed from loop020 by `-15pp` success, `+15pp` crash, and
  `-0.65` mean gates.
- More steps on this same hypothesis are not justified.

W&B/PPO diagnostics:

- Gate-stage and gate-axis proxies improved, but pass/finish conversion did not.
- `passed_gate_rate` stayed flat/down and `finished_rate` remained zero.
- PPO did not show a classic blow-up, but updates look ineffective:
  very low KL, near-zero clip fraction, tiny policy loss, and high entropy.
- Hard eval shows severe command saturation:
  `cmd_tilt_over_limit_frac` about `0.77-0.88`.

Structure/research synthesis:

- loop032 reduces confidence in this specific no-wrapper curriculum lane.
- It does not reject v5 local-obstacle observations overall.
- It does not justify another reward-number tweak.
- The next useful work is local/code diagnosis of train/eval domain gap,
  command saturation, and gate-pass conversion.

## Fresh Diagnostics

After loop032, the main agent fixed the diagnostic-only v5 observation parity
script so it uses the checkpoint observation layout and action low-pass metadata
when constructing the training-side observation probe.

The following diagnostics were run on the loop020 v5 global-best checkpoint:

- v5 observation/event parity:
  `experiments/level3_ppo_loop/diagnostics/level3_obs_event_parity_v5_loop020_25M_summary.json`
- v5 action scaling parity:
  `experiments/level3_ppo_loop/diagnostics/level3_action_scaling_parity_v5_loop020_25M.json`

Results:

- Observation parity is clean:
  - train dim: `68`
  - inference dim: `68`
  - layout: `level3_target_gate_nearest_gate_2obs_local_history_v5`
  - max observation diff: `4.76837158203125e-07`
  - observation failure count: `0`
- Event parity is clean:
  - passed-gate mismatch count: `0`
  - finished mismatch count: `0`
  - timeout mismatch count: `0`
- Action scaling parity is clean:
  - action low/high diff: `0.0`
  - action scale/mean diff: `0.0`
  - sampled scaled-action diff: `0.0`

Interpretation:

- Current evidence does not support a v5 train/inference observation wiring bug.
- Current evidence does not support an action-scaling mismatch.
- The remaining likely failure is behavioral/training-structure related:
  no-wrapper transfer regression, command saturation, weak PPO movement, or
  reward/event incentives that produce gate approach proxies without stable
  passage.

## Required Next Diagnostics

Before another training chunk, produce a short diagnostic packet under
`experiments/level3_ppo_loop/research/` covering:

1. Hard-eval crash taxonomy for loop032 best checkpoint versus loop020 best.
2. Whether loop032 best behaves materially better under its training config
   than under `level3_dr.toml`; this is diagnostic only and cannot count as
   target progress.
3. Command-saturation analysis for loop020, loop031, and loop032:
   compare `cmd_tilt_over_limit_frac`, `mean_action_delta_l2`,
   `mean_max_cmd_tilt_deg`, pass events, and crash target gates.
4. A concrete next hypothesis:
   - `launch_named_structural_lane` only if the diagnosis identifies a specific
     structural/training-structure lever; or
   - `change_reward_or_training_numbers` only if the diagnosis identifies a
     fresh, bounded numeric hypothesis tied to command saturation and gate-pass
     conversion.

Do not use this packet as approval for training. It is a hold packet.
