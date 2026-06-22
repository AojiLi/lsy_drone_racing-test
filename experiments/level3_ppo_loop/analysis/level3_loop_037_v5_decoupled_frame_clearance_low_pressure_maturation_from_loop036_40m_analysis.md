# Level3 PPO Post-Run Analysis: level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m

## Level3 Hard-Eval Scope

- Structural search is allowed only as an explicit named lane.
- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- The main agent must write a decision packet before the next training chunk.
- Allowed next decisions: `stop_target_met`, `hold_for_more_analysis`, `continue_same_hypothesis`, `change_reward_or_training_numbers`, `launch_named_structural_lane`.

## Required Subagent Reviews

- `evaluator_metrics`: Audit checkpoint evidence from the hard evaluator. Focus on success rate, mean successful time, crashes, timeouts, gates, tilt, and whether any checkpoint is promising enough to mature.
- `wandb_ppo_diagnostics`: Audit W&B curves. Focus on train reward, reward components, race metrics, value scale, value loss, KL, clip fraction, entropy, explained variance, SPS, and whether training signals convert into evaluator progress.
- `structure_research_synthesis`: Audit whether the failure is likely reward numbers, observation, controller wiring, reward structure, or training structure. Any framework change must be a named structural lane, source-backed when nontrivial, and must keep the Level3 target track unchanged.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m/level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m_step_020000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 85.00%
- Timeout rate: 15.00%
- Mean gates: 0.6
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.1, 'crash_rate': 0.0, 'timeout_rate': 0.1, 'mean_gates': -0.8}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -289489.90625 | -278071.125 | down |
| train/reward | -119.949295 | -681.918754 | up |
| losses/approx_kl | 0.0 | 1e-06 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 20.30814 | 20.224454 | up |
| losses/explained_variance | 0.774089 | 0.782651 | up |
| losses/value_loss | 8876.714844 | 7810.897298 | up |
| losses/policy_loss | 1e-06 | -1.1e-05 | flat |
| charts/SPS | 13401449.0 | 12911458.666667 | up |
| race/passed_gate_rate | 3.1e-05 | 1e-05 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.013245 | 0.01298 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.428711 | 0.423126 | up |
| race/gate_axis_x | -0.757955 | -0.786105 | up |
| race/gate_centerline_dist | 1.046053 | 1.040803 | up |
| race/gate_plane_dist | 1.047012 | 1.041553 | up |
| race/gate_plane_cross_rate | 0.004852 | 0.004567 | flat |

## Diagnosis

- Branch: `hold_plateau_no_conversion`
- Rationale: Evaluator success/mean_gates did not improve and W&B gate/finish signals did not convert. Do not launch another automatic reward move without a new approved reward-only hypothesis or explicit reward-parameter decision packet.
- PPO instability metrics are diagnostics only; this loop must not tune `learning_rate`, `ent_coef`, `target_kl`, `update_epochs`, `num_minibatches`, `hidden_dim`, or `n_obs`.

## Parameter Recommendation

- None.

- No next training command recommended yet.

## Decision Gate

- Next training is blocked until the main agent synthesizes the analysis and subagent findings into a decision packet under `experiments/level3_ppo_loop/decisions/`.
- If the next move changes observation/controller/reward structure/PPO training structure, the packet must name the structural lane and cite the local or external evidence.

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_037_v5_decoupled_frame_clearance_low_pressure_maturation_from_loop036_40m_analysis.json`
