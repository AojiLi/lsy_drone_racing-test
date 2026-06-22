# Level3 PPO Post-Run Analysis: level3_loop_006_custom_safety_axis_recovery

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_006_custom_safety_axis_recovery/level3_loop_006_custom_safety_axis_recovery_step_020000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.7
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_006_custom_safety_axis_recovery
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 1722.01709 | -3089.298096 | up |
| train/reward | 39.739006 | -19.32908 | up |
| losses/approx_kl | 8.9e-05 | 0.002047 | flat |
| losses/clipfrac | 0.0 | 0.003366 | flat |
| losses/entropy | 4.268688 | 4.264933 | down |
| losses/explained_variance | 0.76522 | 0.75762 | up |
| losses/value_loss | 576.35376 | 643.403931 | up |
| losses/policy_loss | -0.000499 | -0.001632 | flat |
| charts/SPS | 12498230.0 | 11636881.0 | up |
| race/passed_gate_rate | 0.010162 | 0.009598 | flat |
| race/finished_rate | 0.0 | 3.1e-05 | flat |
| race/crashed_rate | 0.010223 | 0.010422 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.166168 | 0.179596 | down |
| race/gate_axis_x | -0.991387 | -1.001735 | down |
| race/gate_centerline_dist | 0.734401 | 0.73415 | down |
| race/obstacle_distance | 0.633004 | 0.639369 | flat |
| race/tilt_angle_deg | 18.745517 | 18.854114 | down |

## Diagnosis

- Branch: `hold_plateau_no_conversion`
- Rationale: Evaluator success/mean_gates did not improve and W&B gate/finish signals did not convert. Do not launch another automatic reward move without a new approved reward-only hypothesis or explicit reward-parameter decision packet.
- PPO instability metrics are diagnostics only; this loop must not tune `learning_rate`, `ent_coef`, `target_kl`, `update_epochs`, `num_minibatches`, `hidden_dim`, or `n_obs`.

## Reward-Only Recommendation

- None.

- No next training command recommended yet.

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_006_custom_safety_axis_recovery_analysis.json`
