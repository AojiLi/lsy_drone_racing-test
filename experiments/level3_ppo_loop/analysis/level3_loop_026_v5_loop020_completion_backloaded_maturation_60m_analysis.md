# Level3 PPO Post-Run Analysis: level3_loop_026_v5_loop020_completion_backloaded_maturation_60m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_026_v5_loop020_completion_backloaded_maturation_60m/level3_loop_026_v5_loop020_completion_backloaded_maturation_60m_step_030000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.05
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.1, 'crash_rate': 0.1, 'timeout_rate': 0.0, 'mean_gates': -1.05}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_026_v5_loop020_completion_backloaded_maturation_60m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -116176.640625 | -112815.058594 | down |
| train/reward | -208.783585 | -327.851126 | down |
| losses/approx_kl | 0.0 | 2e-06 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 21.128979 | 20.997638 | up |
| losses/explained_variance | 0.817839 | 0.82142 | up |
| losses/value_loss | 967.357056 | 1076.413391 | up |
| losses/policy_loss | -1.4e-05 | -1.7e-05 | flat |
| charts/SPS | 21691134.0 | 20103281.5 | up |
| race/passed_gate_rate | 0.0 | 0.0 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.013763 | 0.013206 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.691406 | 0.686768 | up |
| race/gate_axis_x | -0.813157 | -0.788666 | up |
| race/gate_centerline_dist | 1.034883 | 1.029778 | up |
| race/obstacle_distance | 0.602601 | 0.596651 | down |
| race/tilt_angle_deg | 29.478652 | 29.485612 | up |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_026_v5_loop020_completion_backloaded_maturation_60m_analysis.json`
