# Level3 PPO Post-Run Analysis: level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m

## Level3 Hard-Eval Scope

- Structural search is allowed only as an explicit named lane.
- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- The main agent must write a decision packet before the next training chunk.
- Allowed next decisions: `stop_target_met`, `hold_for_more_analysis`, `continue_same_hypothesis`, `change_reward_or_training_numbers`, `launch_named_structural_lane`.

## Required Subagent Reviews

- `evaluator_metrics`: Audit checkpoint evidence from the hard evaluator. Focus on success rate, mean successful time, crashes, timeouts, gates, tilt, and whether any checkpoint is promising enough to mature.
- `wandb_ppo_diagnostics`: Audit W&B curves. Focus on train reward, reward components, race metrics, teacher-retention KL/agreement when present, value scale, value loss, KL, clip fraction, entropy, explained variance, SPS, and whether training signals convert into evaluator progress.
- `structure_research_synthesis`: Audit whether the failure is likely reward numbers, observation, controller wiring, reward structure, or training structure. Any framework change must be a named structural lane, source-backed when nontrivial, and must keep the Level3 target track unchanged.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m/level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m_step_002000000.ckpt`
- Success rate: 18.00%
- Mean successful time: 7.002222222222222
- Crash rate: 82.00%
- Timeout rate: 0.00%
- Mean gates: 1.49
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.01, 'mean_time_s_success': 0.155906, 'crash_rate': 0.01, 'timeout_rate': 0.0, 'mean_gates': -0.08}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -2392.796875 | -527.411418 | up |
| train/reward | 216.914124 | 10.992632 | up |
| losses/approx_kl | 0.003672 | 0.003675 | flat |
| losses/clipfrac | 0.008228 | 0.005892 | flat |
| losses/entropy | 5.60813 | 5.613251 | down |
| losses/explained_variance | 0.728547 | 0.717575 | up |
| losses/value_loss | 479.338684 | 592.094686 | down |
| losses/policy_loss | -0.004151 | -0.003521 | flat |
| charts/SPS | 1580047.0 | 1544562.666667 | up |
| losses/teacher_kl | 0.754162 | 0.75767 | down |
| losses/teacher_action_mse | 0.007609 | 0.00683 | flat |
| retention/teacher_agreement | 0.904858 | 0.917098 | flat |
| retention/sampled_batch_size | 512.0 | 512.0 | flat |
| race/passed_gate_rate | 0.007355 | 0.007528 | flat |
| race/finished_rate | 0.000244 | 0.000254 | flat |
| race/crashed_rate | 0.007843 | 0.008026 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.150421 | 0.162872 | flat |

## V27 Retention Evidence

| Metric | First | Last | Tail mean | Trend |
| --- | ---: | ---: | ---: | --- |
| losses/teacher_kl | 1.054108 | 0.754162 | 0.75767 | down |
| losses/teacher_action_mse | 0.010989 | 0.007609 | 0.00683 | flat |
| retention/teacher_agreement | 0.875 | 0.904858 | 0.917098 | flat |
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_089_structural_v28_gate_conversion_reward_adjust_from_loop088_4m_5m_analysis.json`
