# Level3 PPO Post-Run Analysis: level3_loop_016_loop010_step_curve_maturation_100m

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_016_loop010_step_curve_maturation_100m/level3_loop_016_loop010_step_curve_maturation_100m_step_055000000.ckpt`
- Success rate: 5.00%
- Mean successful time: 6.1
- Crash rate: 95.00%
- Timeout rate: 0.00%
- Mean gates: 0.95
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.05, 'crash_rate': -0.05, 'timeout_rate': 0.0, 'mean_gates': 0.05}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_016_loop010_step_curve_maturation_100m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 26345.939453 | 24601.416992 | up |
| train/reward | -330.096069 | 102.408954 | down |
| losses/approx_kl | 0.002472 | 0.002519 | flat |
| losses/clipfrac | 0.001355 | 0.001782 | flat |
| losses/entropy | 4.95193 | 4.949955 | up |
| losses/explained_variance | 0.785046 | 0.784093 | flat |
| losses/value_loss | 667.991516 | 688.062195 | flat |
| losses/policy_loss | -0.002383 | -0.003329 | flat |
| charts/SPS | 44150447.0 | 43707755.0 | up |
| race/passed_gate_rate | 0.010498 | 0.010361 | flat |
| race/finished_rate | 0.000122 | 0.000107 | flat |
| race/crashed_rate | 0.00943 | 0.00975 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.163605 | 0.175888 | flat |
| race/gate_axis_x | -1.061567 | -1.060867 | down |
| race/gate_centerline_dist | 0.747899 | 0.740721 | flat |
| race/obstacle_distance | 0.678215 | 0.670006 | flat |
| race/tilt_angle_deg | 20.482307 | 20.353886 | up |

## Diagnosis

- Branch: `gate_acquisition`
- Rationale: Low success with low mean gates points to gate acquisition.
- PPO instability metrics are diagnostics only; this loop must not tune `learning_rate`, `ent_coef`, `target_kl`, `update_epochs`, `num_minibatches`, `hidden_dim`, or `n_obs`.

## Reward-Only Recommendation

- `--param gate_stage_coef=13`
- `--param gate_axis_coef=24`
- `--param gate_front_bonus=5`
- `--param gate_bonus=200`
- `--param gate_back_bonus=35`
- `--param finish_bonus=175`
- `--param time_penalty=0.02`

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_016_loop010_step_curve_maturation_100m_analysis.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_016_loop010_step_curve_maturation_100m_analysis.json`
