# Level3 PPO Post-Run Analysis: level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_step_010000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.8
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.05, 'crash_rate': 0.05, 'timeout_rate': 0.0, 'mean_gates': -0.3}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -37776.570312 | -43068.722656 | down |
| train/reward | 108.835159 | -146.28632 | up |
| losses/approx_kl | 0.00011 | 0.001133 | flat |
| losses/clipfrac | 0.0 | 0.000675 | flat |
| losses/entropy | 8.117493 | 8.069097 | up |
| losses/explained_variance | 0.791005 | 0.792882 | flat |
| losses/value_loss | 405.764679 | 468.545095 | down |
| losses/policy_loss | -0.000222 | -0.000725 | flat |
| charts/SPS | 13664397.0 | 12838721.666667 | up |
| race/passed_gate_rate | 0.003754 | 0.003448 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.011597 | 0.011658 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.419495 | 0.430105 | up |
| race/gate_axis_x | -0.853283 | -0.829884 | up |
| race/gate_centerline_dist | 0.76704 | 0.762435 | flat |
| race/obstacle_distance | 0.663405 | 0.658 | flat |
| race/tilt_angle_deg | 19.479157 | 19.012285 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_032_structural_v5_curriculum_gate_obstacle_staged_training_30m_analysis.json`
