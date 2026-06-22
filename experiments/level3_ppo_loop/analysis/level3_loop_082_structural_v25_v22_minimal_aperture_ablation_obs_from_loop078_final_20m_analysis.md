# Level3 PPO Post-Run Analysis: level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m_step_005000000.ckpt`
- Success rate: 10.00%
- Mean successful time: 7.25
- Crash rate: 90.00%
- Timeout rate: 0.00%
- Mean gates: 1.35
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.05, 'mean_time_s_success': 0.076667, 'crash_rate': 0.05, 'timeout_rate': 0.0, 'mean_gates': -0.1}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -44358.578125 | -43617.720052 | down |
| train/reward | -43.297356 | -147.231185 | up |
| losses/approx_kl | 0.005982 | 0.005656 | flat |
| losses/clipfrac | 0.013617 | 0.015291 | flat |
| losses/entropy | 7.260008 | 7.227731 | up |
| losses/explained_variance | 0.793558 | 0.79145 | flat |
| losses/value_loss | 195.615082 | 193.466832 | down |
| losses/policy_loss | -0.002328 | -0.00297 | flat |
| charts/SPS | 5938048.0 | 5600519.666667 | up |
| race/passed_gate_rate | 0.005249 | 0.005391 | flat |
| race/finished_rate | 6.1e-05 | 6.1e-05 | flat |
| race/crashed_rate | 0.008942 | 0.009074 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.206787 | 0.213409 | flat |
| race/gate_axis_x | -0.965585 | -0.995151 | up |
| race/gate_centerline_dist | 0.779985 | 0.78897 | flat |
| race/gate_plane_dist | 0.780126 | 0.788964 | flat |
| race/gate_plane_cross_rate | 0.002991 | 0.002991 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_082_structural_v25_v22_minimal_aperture_ablation_obs_from_loop078_final_20m_analysis.json`
