# Level3 PPO Post-Run Analysis: level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m/level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m_step_020000000.ckpt`
- Success rate: 20.00%
- Mean successful time: 8.165
- Crash rate: 80.00%
- Timeout rate: 0.00%
- Mean gates: 1.6
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.05, 'mean_time_s_success': -0.359, 'crash_rate': 0.05, 'timeout_rate': 0.0, 'mean_gates': -0.4}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -48830.402344 | -46778.488281 | down |
| train/reward | -156.88707 | -133.939025 | up |
| losses/approx_kl | 0.005728 | 0.00459 | flat |
| losses/clipfrac | 0.016125 | 0.012781 | flat |
| losses/entropy | 7.378104 | 7.153138 | up |
| losses/explained_variance | 0.775038 | 0.80014 | flat |
| losses/value_loss | 211.22879 | 185.462662 | down |
| losses/policy_loss | -0.001783 | -0.003516 | flat |
| charts/SPS | 14036463.0 | 12323856.75 | up |
| race/passed_gate_rate | 0.005402 | 0.005386 | flat |
| race/finished_rate | 6.1e-05 | 4.6e-05 | flat |
| race/crashed_rate | 0.009918 | 0.009163 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.225952 | 0.211494 | up |
| race/gate_axis_x | -0.895773 | -0.984289 | up |
| race/gate_centerline_dist | 0.766759 | 0.780942 | up |
| race/gate_plane_dist | 0.76701 | 0.781036 | up |
| race/gate_plane_cross_rate | 0.003052 | 0.003075 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_072_structural_v17_trace_mixed_mature_loop071_20m_to_60m_analysis.json`
