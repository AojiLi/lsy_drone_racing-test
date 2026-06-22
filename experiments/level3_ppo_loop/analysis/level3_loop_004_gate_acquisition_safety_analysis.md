# Level3 PPO Post-Run Analysis: level3_loop_004_gate_acquisition_safety

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_004_gate_acquisition_safety/level3_loop_004_gate_acquisition_safety_step_030000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.8
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_004_gate_acquisition_safety
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 8960.613281 | 6049.829346 | up |
| train/reward | -290.206207 | 39.876796 | down |
| losses/approx_kl | 0.000878 | 0.001236 | flat |
| losses/clipfrac | 7.3e-05 | 0.000181 | flat |
| losses/entropy | 5.436695 | 5.419882 | up |
| losses/explained_variance | 0.758035 | 0.763105 | flat |
| losses/value_loss | 555.446533 | 574.815999 | flat |
| losses/policy_loss | -0.001063 | -0.0026 | flat |
| charts/SPS | 30774807.0 | 29359234.333333 | up |
| race/passed_gate_rate | 0.009827 | 0.009552 | flat |
| race/finished_rate | 0.0 | 2e-05 | flat |
| race/crashed_rate | 0.01062 | 0.010651 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.222778 | 0.200073 | flat |
| race/gate_axis_x | -0.954572 | -0.959109 | down |
| race/gate_centerline_dist | 0.748547 | 0.743236 | flat |
| race/obstacle_distance | 0.651118 | 0.648933 | flat |
| race/tilt_angle_deg | 20.938625 | 20.877674 | up |

## Diagnosis

- Branch: `hold_plateau_no_conversion`
- Rationale: Evaluator success/mean_gates did not improve and W&B gate/finish signals did not convert. Do not launch another automatic reward move without a new human-approved hypothesis.
- PPO instability metrics are diagnostics only; this loop must not tune `learning_rate`, `ent_coef`, `target_kl`, `update_epochs`, `num_minibatches`, `hidden_dim`, or `n_obs`.

## Reward-Only Recommendation

- None.

- No next training command recommended yet.

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_004_gate_acquisition_safety_analysis.json`
