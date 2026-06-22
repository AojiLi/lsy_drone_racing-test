# Level3 PPO Post-Run Analysis: level3_loop_024_v5_action_envelope_75deg_from_loop020_25m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_024_v5_action_envelope_75deg_from_loop020_25m/level3_loop_024_v5_action_envelope_75deg_from_loop020_25m_step_025000000.ckpt`
- Success rate: 5.00%
- Mean successful time: 5.82
- Crash rate: 95.00%
- Timeout rate: 0.00%
- Mean gates: 0.95
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'mean_time_s_success': -0.2, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': -0.15}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_024_v5_action_envelope_75deg_from_loop020_25m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 3803.493896 | -4086.803792 | down |
| train/reward | 104.156723 | -23.158528 | up |
| losses/approx_kl | 0.000117 | 0.001149 | flat |
| losses/clipfrac | 0.0 | 0.000185 | flat |
| losses/entropy | 5.788175 | 5.7701 | up |
| losses/explained_variance | 0.785162 | 0.774106 | flat |
| losses/value_loss | 574.005249 | 714.190938 | flat |
| losses/policy_loss | -0.000445 | -0.001967 | flat |
| charts/SPS | 11092530.0 | 10048470.666667 | up |
| race/passed_gate_rate | 0.008392 | 0.008026 | flat |
| race/finished_rate | 0.0 | 2e-05 | flat |
| race/crashed_rate | 0.009155 | 0.010559 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.185272 | 0.200185 | flat |
| race/gate_axis_x | -1.000605 | -1.005235 | up |
| race/gate_centerline_dist | 0.766398 | 0.764893 | flat |
| race/obstacle_distance | 0.676403 | 0.6671 | flat |
| race/tilt_angle_deg | 20.595003 | 20.345303 | up |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_024_v5_action_envelope_75deg_from_loop020_25m_analysis.json`
