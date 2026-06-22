# Level3 PPO Post-Run Analysis: level3_loop_014_loop010_gate_retention_obstacle_safety

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_014_loop010_gate_retention_obstacle_safety/level3_loop_014_loop010_gate_retention_obstacle_safety_step_025000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.75
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.25, 'timeout_rate': -0.25, 'mean_gates': 0.4}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_014_loop010_gate_retention_obstacle_safety
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 13445.904297 | 13929.518555 | up |
| train/reward | 52.519691 | 75.9636 | up |
| losses/approx_kl | 5.7e-05 | 0.000775 | flat |
| losses/clipfrac | 0.0 | 0.000305 | flat |
| losses/entropy | 4.952176 | 4.951403 | up |
| losses/explained_variance | 0.788661 | 0.784791 | up |
| losses/value_loss | 628.286377 | 654.440511 | down |
| losses/policy_loss | -0.000593 | -0.00102 | flat |
| charts/SPS | 16173771.0 | 15564531.0 | up |
| race/passed_gate_rate | 0.009705 | 0.009837 | flat |
| race/finished_rate | 6.1e-05 | 8.1e-05 | flat |
| race/crashed_rate | 0.010406 | 0.010264 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.201782 | 0.190664 | flat |
| race/gate_axis_x | -1.029012 | -1.016104 | down |
| race/gate_centerline_dist | 0.717303 | 0.729339 | flat |
| race/obstacle_distance | 0.659308 | 0.66702 | flat |
| race/tilt_angle_deg | 19.689085 | 19.779736 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_014_loop010_gate_retention_obstacle_safety_analysis.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_014_loop010_gate_retention_obstacle_safety_analysis.json`
