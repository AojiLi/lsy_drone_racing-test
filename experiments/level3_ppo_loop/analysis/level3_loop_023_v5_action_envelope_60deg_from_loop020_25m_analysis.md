# Level3 PPO Post-Run Analysis: level3_loop_023_v5_action_envelope_60deg_from_loop020_25m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_023_v5_action_envelope_60deg_from_loop020_25m/level3_loop_023_v5_action_envelope_60deg_from_loop020_25m_final.ckpt`
- Success rate: 5.00%
- Mean successful time: 6.02
- Crash rate: 95.00%
- Timeout rate: 0.00%
- Mean gates: 1.1
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'mean_time_s_success': -0.66, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_023_v5_action_envelope_60deg_from_loop020_25m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 1026.337158 | -11.807373 | down |
| train/reward | 63.681087 | 14.544766 | up |
| losses/approx_kl | 0.000138 | 0.000558 | flat |
| losses/clipfrac | 0.0 | 9.6e-05 | flat |
| losses/entropy | 6.021063 | 6.016026 | up |
| losses/explained_variance | 0.783583 | 0.777863 | flat |
| losses/value_loss | 619.705872 | 663.591532 | down |
| losses/policy_loss | -0.000571 | -0.000824 | flat |
| charts/SPS | 10420724.0 | 10320847.333333 | up |
| race/passed_gate_rate | 0.008209 | 0.008128 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.010071 | 0.009949 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.202179 | 0.199148 | flat |
| race/gate_axis_x | -1.02125 | -1.011093 | up |
| race/gate_centerline_dist | 0.769361 | 0.767918 | flat |
| race/obstacle_distance | 0.683247 | 0.679128 | flat |
| race/tilt_angle_deg | 19.921601 | 19.941225 | up |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_023_v5_action_envelope_60deg_from_loop020_25m_analysis.json`
