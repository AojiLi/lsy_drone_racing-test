# Level3 PPO Post-Run Analysis: level3_loop_005_auto_precision_low_pressure

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_005_auto_precision_low_pressure/level3_loop_005_auto_precision_low_pressure_final.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.7
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': -0.1}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_005_auto_precision_low_pressure
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -14350.838867 | -20679.635091 | down |
| train/reward | 147.69902 | 28.567924 | up |
| losses/approx_kl | 0.000315 | 0.000395 | flat |
| losses/clipfrac | 6e-06 | 8e-06 | flat |
| losses/entropy | 5.943738 | 5.939332 | up |
| losses/explained_variance | 0.767198 | 0.776466 | flat |
| losses/value_loss | 547.984192 | 553.027751 | flat |
| losses/policy_loss | -0.001016 | -0.000889 | flat |
| charts/SPS | 11940385.0 | 11608229.666667 | up |
| race/passed_gate_rate | 0.007477 | 0.006805 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.012054 | 0.01239 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.250519 | 0.25061 | flat |
| race/gate_axis_x | -0.885843 | -0.874879 | down |
| race/gate_centerline_dist | 0.765852 | 0.758725 | flat |
| race/obstacle_distance | 0.622314 | 0.620707 | flat |
| race/tilt_angle_deg | 20.700885 | 20.763823 | up |

## Diagnosis

- Branch: `hold_plateau_no_conversion`
- Rationale: Evaluator success/mean_gates did not improve and W&B gate/finish signals did not convert. Do not launch another automatic reward move without a new approved reward-only hypothesis or explicit reward-parameter decision packet.
- PPO instability metrics are diagnostics only; this loop must not tune `learning_rate`, `ent_coef`, `target_kl`, `update_epochs`, `num_minibatches`, `hidden_dim`, or `n_obs`.

## Reward-Only Recommendation

- None.

- No next training command recommended yet.

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_005_auto_precision_low_pressure_analysis.json`
