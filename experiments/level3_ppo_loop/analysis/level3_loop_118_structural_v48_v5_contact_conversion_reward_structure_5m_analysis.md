# Level3 PPO Post-Run Analysis: level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m/level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m_step_001000000.ckpt`
- Success rate: 16.00%
- Mean successful time: 6.51625
- Crash rate: 84.00%
- Timeout rate: 0.00%
- Mean gates: 1.5
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.04, 'mean_time_s_success': -0.54775, 'crash_rate': 0.04, 'timeout_rate': 0.0, 'mean_gates': -0.08}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -93853.039062 | -93853.039062 | up |
| train/reward | -338.419373 | -339.903936 | down |
| losses/approx_kl | 3.2e-05 | 3.2e-05 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 4.661826 | 4.661826 | up |
| losses/explained_variance | 0.431928 | 0.431928 | flat |
| losses/value_loss | 6850.28418 | 6850.28418 | up |
| losses/policy_loss | -0.000174 | -0.000174 | flat |
| charts/SPS | 528840.0 | 528840.0 | up |
| losses/teacher_kl | 0.0 | 0.0 | flat |
| losses/teacher_action_mse | 0.0 | 0.0 | flat |
| retention/sampled_batch_size | 0.0 | 0.0 | flat |
| race/passed_gate_rate | 0.005127 | 0.005127 | flat |
| race/finished_rate | 9.2e-05 | 9.2e-05 | flat |
| race/crashed_rate | 0.007507 | 0.007507 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.060974 | 0.060974 | flat |
| race/gate_axis_x | -1.158371 | -1.158371 | down |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_118_structural_v48_v5_contact_conversion_reward_structure_5m_analysis.json`
