# Level3 PPO Post-Run Analysis: level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m_step_015000000.ckpt`
- Success rate: 5.00%
- Mean successful time: 5.08
- Crash rate: 95.00%
- Timeout rate: 0.00%
- Mean gates: 0.9
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'mean_time_s_success': -2.16, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': -0.2}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -27950.095703 | -23800.424479 | down |
| train/reward | -64.61908 | -66.464623 | up |
| losses/approx_kl | 0.001235 | 0.002362 | flat |
| losses/clipfrac | 6.1e-05 | 0.002159 | flat |
| losses/entropy | 8.677567 | 8.478231 | up |
| losses/explained_variance | 0.780873 | 0.77488 | flat |
| losses/value_loss | 665.552979 | 582.855204 | flat |
| losses/policy_loss | -0.001647 | -0.000511 | flat |
| charts/SPS | 6566427.0 | 5675665.333333 | up |
| race/passed_gate_rate | 0.003784 | 0.003805 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.012329 | 0.011749 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.345001 | 0.342153 | up |
| race/gate_axis_x | -0.863852 | -0.863472 | up |
| race/gate_centerline_dist | 0.773763 | 0.778545 | flat |
| race/obstacle_distance | 0.622101 | 0.625268 | down |
| race/tilt_angle_deg | 17.682585 | 17.199802 | down |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_034_structural_v5_mild_lowpass_pass_conversion_controller_20m_analysis.json`
