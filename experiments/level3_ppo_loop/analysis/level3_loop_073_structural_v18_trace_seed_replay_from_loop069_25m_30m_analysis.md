# Level3 PPO Post-Run Analysis: level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m/level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m_step_025000000.ckpt`
- Success rate: 15.00%
- Mean successful time: 7.466666666666666
- Crash rate: 85.00%
- Timeout rate: 0.00%
- Mean gates: 1.6
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.05, 'mean_time_s_success': -0.698333, 'crash_rate': 0.05, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -28904.019531 | -30814.667969 | down |
| train/reward | -93.969666 | -132.758921 | up |
| losses/approx_kl | 0.004577 | 0.004921 | flat |
| losses/clipfrac | 0.012683 | 0.014514 | flat |
| losses/entropy | 5.684587 | 5.673714 | up |
| losses/explained_variance | 0.774989 | 0.735074 | up |
| losses/value_loss | 194.90509 | 228.409653 | flat |
| losses/policy_loss | -0.004865 | -0.006115 | flat |
| charts/SPS | 7490721.0 | 7395761.5 | up |
| race/passed_gate_rate | 0.007385 | 0.006561 | flat |
| race/finished_rate | 6.1e-05 | 0.000214 | flat |
| race/crashed_rate | 0.007507 | 0.007599 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.199524 | 0.204987 | flat |
| race/gate_axis_x | -1.035582 | -1.042173 | flat |
| race/gate_centerline_dist | 0.729459 | 0.745745 | flat |
| race/gate_plane_dist | 0.729414 | 0.745676 | flat |
| race/gate_plane_cross_rate | 0.002411 | 0.002502 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_073_structural_v18_trace_seed_replay_from_loop069_25m_30m_analysis.json`
