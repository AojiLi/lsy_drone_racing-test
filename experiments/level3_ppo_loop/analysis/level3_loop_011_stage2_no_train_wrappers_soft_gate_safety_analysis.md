# Level3 PPO Post-Run Analysis: level3_loop_011_stage2_no_train_wrappers_soft_gate_safety

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_011_stage2_no_train_wrappers_soft_gate_safety/level3_loop_011_stage2_no_train_wrappers_soft_gate_safety_step_025000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.85
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.05, 'crash_rate': 0.05, 'timeout_rate': 0.0, 'mean_gates': 0.05}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_011_stage2_no_train_wrappers_soft_gate_safety
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 17705.730469 | 21387.264323 | up |
| train/reward | -111.793701 | 50.000566 | down |
| losses/approx_kl | 0.000227 | 0.002576 | flat |
| losses/clipfrac | 0.0 | 0.002924 | flat |
| losses/entropy | 4.671977 | 4.660469 | flat |
| losses/explained_variance | 0.806048 | 0.801952 | flat |
| losses/value_loss | 566.948059 | 570.445719 | down |
| losses/policy_loss | -0.000862 | -0.003074 | flat |
| charts/SPS | 15962876.0 | 14971473.666667 | up |
| race/passed_gate_rate | 0.009979 | 0.010712 | flat |
| race/finished_rate | 0.0 | 2e-05 | flat |
| race/crashed_rate | 0.00946 | 0.01001 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.17215 | 0.16392 | flat |
| race/gate_axis_x | -1.077771 | -1.037577 | down |
| race/gate_centerline_dist | 0.751903 | 0.731704 | flat |
| race/obstacle_distance | 0.679673 | 0.664168 | up |
| race/tilt_angle_deg | 20.312134 | 20.298808 | up |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_011_stage2_no_train_wrappers_soft_gate_safety_analysis.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_011_stage2_no_train_wrappers_soft_gate_safety_analysis.json`
