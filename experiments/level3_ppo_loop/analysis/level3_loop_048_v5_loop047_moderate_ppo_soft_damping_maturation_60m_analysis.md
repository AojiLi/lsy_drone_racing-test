# Level3 PPO Post-Run Analysis: level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m/level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m_final.ckpt`
- Success rate: 15.00%
- Mean successful time: 6.406666666666666
- Crash rate: 85.00%
- Timeout rate: 0.00%
- Mean gates: 1.25
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'mean_time_s_success': 0.086667, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 44417.890625 | 45364.139323 | flat |
| train/reward | -73.180649 | 150.023795 | up |
| losses/approx_kl | 0.003559 | 0.003978 | flat |
| losses/clipfrac | 0.002803 | 0.006516 | flat |
| losses/entropy | 4.649404 | 4.64278 | up |
| losses/explained_variance | 0.772415 | 0.74791 | flat |
| losses/value_loss | 863.618164 | 1016.087891 | flat |
| losses/policy_loss | -0.002738 | -0.002886 | flat |
| charts/SPS | 10099099.0 | 9744053.666667 | up |
| race/passed_gate_rate | 0.009521 | 0.010081 | flat |
| race/finished_rate | 3.1e-05 | 0.000142 | flat |
| race/crashed_rate | 0.00769 | 0.008067 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.145935 | 0.143717 | flat |
| race/gate_axis_x | -1.224355 | -1.170034 | down |
| race/gate_centerline_dist | 0.76128 | 0.758414 | flat |
| race/gate_plane_dist | 0.761372 | 0.758573 | flat |
| race/gate_plane_cross_rate | 0.001984 | 0.002228 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_048_v5_loop047_moderate_ppo_soft_damping_maturation_60m_analysis.json`
