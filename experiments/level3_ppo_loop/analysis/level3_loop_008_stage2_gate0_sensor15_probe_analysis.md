# Level3 PPO Post-Run Analysis: level3_loop_008_stage2_gate0_sensor15_probe

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_008_stage2_gate0_sensor15_probe/level3_loop_008_stage2_gate0_sensor15_probe_step_015000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.75
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_008_stage2_gate0_sensor15_probe
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -2077.271729 | -248.752686 | down |
| train/reward | 868.710693 | 13.559893 | up |
| losses/approx_kl | 0.000111 | 0.00222 | flat |
| losses/clipfrac | 0.0 | 0.002805 | flat |
| losses/entropy | 5.173088 | 5.167545 | up |
| losses/explained_variance | 0.757518 | 0.757146 | flat |
| losses/value_loss | 477.252319 | 448.830612 | up |
| losses/policy_loss | -0.000444 | -0.003292 | flat |
| charts/SPS | 12403107.0 | 11894469.0 | up |
| race/passed_gate_rate | 0.009064 | 0.009338 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.01123 | 0.011185 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.164856 | 0.161118 | down |
| race/gate_axis_x | -0.933406 | -0.942158 | flat |
| race/gate_centerline_dist | 0.768608 | 0.754374 | flat |
| race/obstacle_distance | 0.64559 | 0.63762 | flat |
| race/tilt_angle_deg | 20.681856 | 20.616402 | flat |

## Diagnosis

- Branch: `hold_plateau_no_conversion`
- Rationale: Evaluator success/mean_gates did not improve and W&B gate/finish signals did not convert. Do not launch another automatic reward move without a new approved reward-only hypothesis or explicit reward-parameter decision packet.
- PPO instability metrics are diagnostics only; this loop must not tune `learning_rate`, `ent_coef`, `target_kl`, `update_epochs`, `num_minibatches`, `hidden_dim`, or `n_obs`.

## Reward-Only Recommendation

- None.

- No next training command recommended yet.

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_008_stage2_gate0_sensor15_probe_analysis.json`
