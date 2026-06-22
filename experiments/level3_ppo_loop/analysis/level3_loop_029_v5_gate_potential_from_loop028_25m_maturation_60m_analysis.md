# Level3 PPO Post-Run Analysis: level3_loop_029_v5_gate_potential_from_loop028_25m_maturation_60m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_029_v5_gate_potential_from_loop028_25m_maturation_60m/level3_loop_029_v5_gate_potential_from_loop028_25m_maturation_60m_step_030000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.7
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.15, 'crash_rate': 0.15, 'timeout_rate': 0.0, 'mean_gates': -0.45}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_029_v5_gate_potential_from_loop028_25m_maturation_60m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -97364.859375 | -98220.648438 | down |
| train/reward | -106.167557 | -180.08455 | up |
| losses/approx_kl | 0.000188 | 0.000643 | flat |
| losses/clipfrac | 0.0 | 2.3e-05 | flat |
| losses/entropy | 22.349642 | 22.150861 | up |
| losses/explained_variance | 0.788585 | 0.819491 | up |
| losses/value_loss | 494.394775 | 447.346512 | up |
| losses/policy_loss | 0.000148 | -0.001011 | flat |
| charts/SPS | 20411462.0 | 19094341.25 | up |
| race/passed_gate_rate | 0.000183 | 0.000122 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.015533 | 0.015358 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.608704 | 0.610779 | up |
| race/gate_axis_x | -0.759948 | -0.787167 | up |
| race/gate_centerline_dist | 0.977635 | 0.986484 | up |
| race/obstacle_distance | 0.594498 | 0.608697 | flat |
| race/tilt_angle_deg | 20.653237 | 20.154235 | up |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_029_v5_gate_potential_from_loop028_25m_maturation_60m_analysis.json`
