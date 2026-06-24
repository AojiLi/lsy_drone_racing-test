# Level3 PPO Post-Run Analysis: level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery/level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery_step_005000000.ckpt`
- Success rate: 15.00%
- Mean successful time: 6.741333333333333
- Crash rate: 85.00%
- Timeout rate: 0.00%
- Mean gates: 1.5
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.01, 'mean_time_s_success': 0.225083, 'crash_rate': 0.01, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -20779.666016 | -20779.666016 | down |
| train/reward | -142.543625 | -88.053149 | down |
| losses/approx_kl | 2e-06 | 2e-06 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 5.381611 | 5.381611 | up |
| losses/explained_variance | 0.770792 | 0.770792 | flat |
| losses/value_loss | 681.335388 | 681.335388 | up |
| losses/policy_loss | -9.8e-05 | -9.8e-05 | flat |
| charts/SPS | 1601601.0 | 1601601.0 | up |
| losses/teacher_kl | 0.0 | 0.0 | flat |
| losses/teacher_action_mse | 0.0 | 0.0 | flat |
| retention/sampled_batch_size | 0.0 | 0.0 | flat |
| race/passed_gate_rate | 0.004791 | 0.004791 | flat |
| race/finished_rate | 0.000153 | 0.000153 | flat |
| race/crashed_rate | 0.007996 | 0.007996 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.061035 | 0.061035 | flat |
| race/gate_axis_x | -1.065142 | -1.065142 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_120_structural_v49_hidden512_45m_to_60m_recovery_analysis.json`
