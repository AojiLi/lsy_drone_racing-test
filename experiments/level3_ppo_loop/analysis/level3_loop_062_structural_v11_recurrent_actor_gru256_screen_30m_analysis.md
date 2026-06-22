# Level3 PPO Post-Run Analysis: level3_loop_062_structural_v11_recurrent_actor_gru256_screen_30m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_062_structural_v11_recurrent_actor_gru256_screen_30m/level3_loop_062_structural_v11_recurrent_actor_gru256_screen_30m_step_010000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 55.00%
- Timeout rate: 45.00%
- Mean gates: 0.1
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.1, 'crash_rate': -0.35, 'timeout_rate': 0.45, 'mean_gates': -1.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_062_structural_v11_recurrent_actor_gru256_screen_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -59490.957031 | -58208.532552 | up |
| train/reward | -145.316086 | -343.324944 | down |
| losses/approx_kl | 1e-06 | 1.2e-05 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 1.768674 | 1.767924 | up |
| losses/explained_variance | 0.657482 | 0.660869 | up |
| losses/value_loss | 248.215729 | 204.92424 | down |
| losses/policy_loss | -4.6e-05 | -1.3e-05 | flat |
| charts/SPS | 9744167.0 | 9681682.0 | up |
| race/passed_gate_rate | 0.0 | 0.0 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.005707 | 0.005575 | flat |
| race/timeout_rate | 0.000305 | 0.000163 | flat |
| race/gate_stage | 0.772461 | 0.771891 | up |
| race/gate_axis_x | -0.81055 | -0.830978 | flat |
| race/gate_centerline_dist | 1.028959 | 1.022609 | down |
| race/gate_plane_dist | 1.02924 | 1.022888 | down |
| race/gate_plane_cross_rate | 0.001892 | 0.001841 | flat |

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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_062_structural_v11_recurrent_actor_gru256_screen_30m_analysis.json`
