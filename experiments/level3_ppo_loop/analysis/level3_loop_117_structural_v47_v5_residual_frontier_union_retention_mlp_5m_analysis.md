# Level3 PPO Post-Run Analysis: level3_loop_117_structural_v47_v5_residual_frontier_union_retention_mlp_5m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_117_structural_v47_v5_residual_frontier_union_retention_mlp_5m/level3_loop_117_structural_v47_v5_residual_frontier_union_retention_mlp_5m_step_003000000.ckpt`
- Success rate: 20.00%
- Mean successful time: 7.063999999999998
- Crash rate: 80.00%
- Timeout rate: 0.00%
- Mean gates: 1.58
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'mean_time_s_success': 0.123, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': -0.02}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_117_structural_v47_v5_residual_frontier_union_retention_mlp_5m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -3830.595703 | -3830.595703 | down |
| train/reward | -147.568298 | -17.258921 | down |
| losses/approx_kl | 7e-06 | 7e-06 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 4.489318 | 4.489318 | flat |
| losses/explained_variance | 0.757224 | 0.757224 | flat |
| losses/value_loss | 598.358215 | 598.358215 | down |
| losses/policy_loss | -0.000131 | -0.000131 | flat |
| charts/SPS | 563992.0 | 563992.0 | up |
| losses/teacher_kl | 0.044482 | 0.044482 | flat |
| losses/teacher_action_mse | 0.010212 | 0.010212 | flat |
| retention/teacher_agreement | 0.890039 | 0.890039 | flat |
| retention/sampled_batch_size | 512.0 | 512.0 | flat |
| race/passed_gate_rate | 0.005585 | 0.005585 | flat |
| race/finished_rate | 0.000122 | 0.000122 | flat |
| race/crashed_rate | 0.006989 | 0.006989 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.055695 | 0.055695 | flat |

## V27 Retention Evidence

| Metric | First | Last | Tail mean | Trend |
| --- | ---: | ---: | ---: | --- |
| losses/teacher_kl | 0.049981 | 0.044482 | 0.044482 | flat |
| losses/teacher_action_mse | 0.011354 | 0.010212 | 0.010212 | flat |
| retention/teacher_agreement | 0.871606 | 0.890039 | 0.890039 | flat |
| retention/sampled_batch_size | 512.0 | 512.0 | 512.0 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_117_structural_v47_v5_residual_frontier_union_retention_mlp_5m_analysis.json`
