# Level3 PPO Post-Run Analysis: level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m/level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m_step_010000000.ckpt`
- Success rate: 10.00%
- Mean successful time: 6.4
- Crash rate: 90.00%
- Timeout rate: 0.00%
- Mean gates: 1.25
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.05, 'mean_time_s_success': 0.006667, 'crash_rate': 0.05, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -22022.724609 | -16181.213216 | down |
| train/reward | 342.47467 | -47.482804 | up |
| losses/approx_kl | 0.004297 | 0.004348 | flat |
| losses/clipfrac | 0.013397 | 0.008099 | flat |
| losses/entropy | 5.176125 | 5.080561 | up |
| losses/explained_variance | 0.777267 | 0.757467 | up |
| losses/value_loss | 600.014648 | 580.419963 | up |
| losses/policy_loss | -0.007075 | -0.004278 | flat |
| charts/SPS | 6992929.0 | 6270596.0 | up |
| race/passed_gate_rate | 0.0065 | 0.007568 | flat |
| race/finished_rate | 6.1e-05 | 0.000112 | flat |
| race/crashed_rate | 0.007385 | 0.00826 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.176392 | 0.169128 | flat |
| race/gate_axis_x | -1.098585 | -1.092452 | up |
| race/gate_centerline_dist | 0.765701 | 0.765885 | flat |
| race/gate_plane_dist | 0.765949 | 0.766032 | flat |
| race/gate_plane_cross_rate | 0.002838 | 0.002899 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m_analysis.json`
