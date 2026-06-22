# Level3 PPO Post-Run Analysis: level3_loop_098_structural_v31d_longer_rollout_mature_loop097_12m_to_30m

## Level3 Hard-Eval Scope

- Structural search is allowed only as an explicit named lane.
- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3.toml`.
- The main agent must write a decision packet before the next training chunk.
- Allowed next decisions: `stop_target_met`, `hold_for_more_analysis`, `continue_same_hypothesis`, `change_reward_or_training_numbers`, `launch_named_structural_lane`.

## Required Subagent Reviews

- `evaluator_metrics`: Audit checkpoint evidence from the hard evaluator. Focus on success rate, mean successful time, crashes, timeouts, gates, tilt, and whether any checkpoint is promising enough to mature.
- `wandb_ppo_diagnostics`: Audit W&B curves. Focus on train reward, reward components, race metrics, teacher-retention KL/agreement when present, value scale, value loss, KL, clip fraction, entropy, explained variance, SPS, and whether training signals convert into evaluator progress.
- `structure_research_synthesis`: Audit whether the failure is likely reward numbers, observation, controller wiring, reward structure, or training structure. Any framework change must be a named structural lane, source-backed when nontrivial, and must keep the Level3 target track unchanged.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_098_structural_v31d_longer_rollout_mature_loop097_12m_to_30m/level3_loop_098_structural_v31d_longer_rollout_mature_loop097_12m_to_30m_step_012000000.ckpt`
- Success rate: 19.00%
- Mean successful time: 7.4957894736842094
- Crash rate: 81.00%
- Timeout rate: 0.00%
- Mean gates: 1.63
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.01, 'mean_time_s_success': 0.440789, 'crash_rate': 0.01, 'timeout_rate': 0.0, 'mean_gates': -0.03}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_098_structural_v31d_longer_rollout_mature_loop097_12m_to_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -32453.150391 | -32453.150391 | down |
| train/reward | -143.154724 | -120.952969 | up |
| losses/approx_kl | 0.004075 | 0.004075 | flat |
| losses/clipfrac | 0.006116 | 0.006116 | flat |
| losses/entropy | 4.194527 | 4.194527 | flat |
| losses/explained_variance | 0.791185 | 0.791185 | flat |
| losses/value_loss | 220.589569 | 220.589569 | down |
| losses/policy_loss | -0.006577 | -0.006577 | flat |
| charts/SPS | 836403.0 | 836403.0 | up |
| losses/teacher_kl | 0.0 | 0.0 | flat |
| losses/teacher_action_mse | 0.0 | 0.0 | flat |
| retention/sampled_batch_size | 0.0 | 0.0 | flat |
| race/passed_gate_rate | 0.005432 | 0.005432 | flat |
| race/finished_rate | 0.000122 | 0.000122 | flat |
| race/crashed_rate | 0.007294 | 0.007294 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.067078 | 0.067078 | flat |
| race/gate_axis_x | -1.138469 | -1.138469 | flat |

## V27 Retention Evidence

| Metric | First | Last | Tail mean | Trend |
| --- | ---: | ---: | ---: | --- |
| losses/teacher_kl | 0.0 | 0.0 | 0.0 | flat |
| losses/teacher_action_mse | 0.0 | 0.0 | 0.0 | flat |
| retention/sampled_batch_size | 0.0 | 0.0 | 0.0 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_098_structural_v31d_longer_rollout_mature_loop097_12m_to_30m_analysis.json`
