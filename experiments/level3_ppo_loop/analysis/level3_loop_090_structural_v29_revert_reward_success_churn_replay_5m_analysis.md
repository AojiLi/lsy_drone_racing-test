# Level3 PPO Post-Run Analysis: level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m_step_003000000.ckpt`
- Success rate: 14.00%
- Mean successful time: 6.719999999999999
- Crash rate: 86.00%
- Timeout rate: 0.00%
- Mean gates: 1.39
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.04, 'mean_time_s_success': -0.282222, 'crash_rate': 0.04, 'timeout_rate': 0.0, 'mean_gates': -0.1}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -29090.339844 | -27607.972656 | up |
| train/reward | -30.380028 | -123.552743 | up |
| losses/approx_kl | 0.003852 | 0.004019 | flat |
| losses/clipfrac | 0.006561 | 0.006326 | flat |
| losses/entropy | 5.487065 | 5.489504 | down |
| losses/explained_variance | 0.732347 | 0.717009 | flat |
| losses/value_loss | 233.677597 | 219.053947 | up |
| losses/policy_loss | -0.003837 | -0.002137 | flat |
| charts/SPS | 1475380.0 | 1538392.5 | up |
| losses/teacher_kl | 0.709561 | 0.710741 | down |
| losses/teacher_action_mse | 0.010372 | 0.00939 | flat |
| retention/teacher_agreement | 0.892395 | 0.901733 | up |
| retention/sampled_batch_size | 512.0 | 512.0 | flat |
| race/passed_gate_rate | 0.007812 | 0.008316 | flat |
| race/finished_rate | 0.000244 | 0.000275 | flat |
| race/crashed_rate | 0.007843 | 0.007858 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.179779 | 0.175659 | flat |

## V27 Retention Evidence

| Metric | First | Last | Tail mean | Trend |
| --- | ---: | ---: | ---: | --- |
| losses/teacher_kl | 1.033211 | 0.709561 | 0.710741 | down |
| losses/teacher_action_mse | 0.012242 | 0.010372 | 0.00939 | flat |
| retention/teacher_agreement | 0.860596 | 0.892395 | 0.901733 | up |
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_090_structural_v29_revert_reward_success_churn_replay_5m_analysis.json`
