# Level3 PPO Post-Run Analysis: level3_loop_009_stage2_gate_box_reward_geometry

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_009_stage2_gate_box_reward_geometry/level3_loop_009_stage2_gate_box_reward_geometry_step_020000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.75
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_009_stage2_gate_box_reward_geometry
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 2578.07373 | 377.584534 | down |
| train/reward | -88.113701 | 17.657823 | down |
| losses/approx_kl | 3.9e-05 | 0.001564 | flat |
| losses/clipfrac | 0.0 | 0.001108 | flat |
| losses/entropy | 5.376494 | 5.369866 | up |
| losses/explained_variance | 0.783279 | 0.781183 | up |
| losses/value_loss | 566.607056 | 559.807953 | down |
| losses/policy_loss | -0.000255 | -0.001333 | flat |
| charts/SPS | 11983283.0 | 11342155.0 | up |
| race/passed_gate_rate | 0.009644 | 0.009155 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.011444 | 0.011185 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.207489 | 0.206818 | flat |
| race/gate_axis_x | -0.92352 | -0.957882 | down |
| race/gate_centerline_dist | 0.736974 | 0.740199 | flat |
| race/obstacle_distance | 0.622708 | 0.635519 | flat |
| race/tilt_angle_deg | 20.540987 | 20.383037 | flat |

## Diagnosis

- Branch: `hold_plateau_no_conversion`
- Rationale: Evaluator success/mean_gates did not improve and W&B gate/finish signals did not convert. Do not launch another automatic reward move without a new approved reward-only hypothesis or explicit reward-parameter decision packet.
- PPO instability metrics are diagnostics only; this loop must not tune `learning_rate`, `ent_coef`, `target_kl`, `update_epochs`, `num_minibatches`, `hidden_dim`, or `n_obs`.

## Reward-Only Recommendation

- None.

- No next training command recommended yet.

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_009_stage2_gate_box_reward_geometry_analysis.json`
