# Level3 PPO Post-Run Analysis: level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m_step_015000000.ckpt`
- Success rate: 10.00%
- Mean successful time: 5.789999999999999
- Crash rate: 90.00%
- Timeout rate: 0.00%
- Mean gates: 1.15
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'mean_time_s_success': 0.54, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 13995.886719 | 13447.651367 | up |
| train/reward | -102.792114 | 56.884178 | up |
| losses/approx_kl | 0.00057 | 0.001497 | flat |
| losses/clipfrac | 1.2e-05 | 0.003178 | down |
| losses/entropy | 3.182586 | 3.178357 | down |
| losses/explained_variance | 0.698241 | 0.704863 | flat |
| losses/value_loss | 364.198517 | 364.619598 | down |
| losses/policy_loss | -0.000725 | -0.001942 | flat |
| charts/SPS | 10791659.0 | 10324085.333333 | up |
| race/passed_gate_rate | 0.011353 | 0.011058 | flat |
| race/finished_rate | 0.000427 | 0.000427 | flat |
| race/crashed_rate | 0.007843 | 0.00766 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.138947 | 0.141388 | flat |
| race/gate_axis_x | -1.102385 | -1.100605 | down |
| race/gate_centerline_dist | 0.718525 | 0.721714 | flat |
| race/obstacle_distance | 0.666476 | 0.670005 | flat |
| race/tilt_angle_deg | 18.303401 | 18.287272 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_019_v5_remote_scale_rebalance_from_loop018_30m_analysis.json`
