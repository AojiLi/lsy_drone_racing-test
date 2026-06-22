# Level3 PPO Post-Run Analysis: level3_loop_046_v7_10m_stability_retune_from_loop045_30m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_046_v7_10m_stability_retune_from_loop045_30m/level3_loop_046_v7_10m_stability_retune_from_loop045_30m_step_020000000.ckpt`
- Success rate: 10.00%
- Mean successful time: 5.95
- Crash rate: 90.00%
- Timeout rate: 0.00%
- Mean gates: 1.05
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.05, 'mean_time_s_success': -0.043333, 'crash_rate': 0.05, 'timeout_rate': 0.0, 'mean_gates': -0.15}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_046_v7_10m_stability_retune_from_loop045_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -51670.417969 | -54054.103516 | down |
| train/reward | -117.759041 | -96.128973 | down |
| losses/approx_kl | 2e-06 | 4e-06 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 9.675545 | 9.675072 | up |
| losses/explained_variance | 0.794957 | 0.797278 | flat |
| losses/value_loss | 614.457153 | 651.528748 | down |
| losses/policy_loss | -6.9e-05 | -0.000104 | flat |
| charts/SPS | 10039274.0 | 10042816.0 | up |
| race/passed_gate_rate | 0.003174 | 0.002975 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.012085 | 0.012451 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.389801 | 0.39064 | up |
| race/gate_axis_x | -0.859127 | -0.855414 | up |
| race/gate_centerline_dist | 0.800177 | 0.800078 | flat |
| race/gate_plane_dist | 0.800185 | 0.800215 | flat |
| race/gate_plane_cross_rate | 0.003662 | 0.003922 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_046_v7_10m_stability_retune_from_loop045_30m_analysis.json`
