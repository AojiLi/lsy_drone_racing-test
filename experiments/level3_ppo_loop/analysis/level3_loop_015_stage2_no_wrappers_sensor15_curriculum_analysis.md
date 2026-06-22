# Level3 PPO Post-Run Analysis: level3_loop_015_stage2_no_wrappers_sensor15_curriculum

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_015_stage2_no_wrappers_sensor15_curriculum/level3_loop_015_stage2_no_wrappers_sensor15_curriculum_step_015000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.9
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.15}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_015_stage2_no_wrappers_sensor15_curriculum
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 26681.851562 | 25934.116211 | flat |
| train/reward | 39.726013 | 97.176477 | up |
| losses/approx_kl | 0.000127 | 0.002056 | flat |
| losses/clipfrac | 0.0 | 0.000974 | flat |
| losses/entropy | 4.936977 | 4.932241 | up |
| losses/explained_variance | 0.783221 | 0.787935 | down |
| losses/value_loss | 760.705933 | 718.717041 | up |
| losses/policy_loss | -0.000314 | -0.001599 | flat |
| charts/SPS | 16246435.0 | 15177212.5 | up |
| race/passed_gate_rate | 0.011292 | 0.010941 | flat |
| race/finished_rate | 6.1e-05 | 3.1e-05 | flat |
| race/crashed_rate | 0.010376 | 0.009979 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.166046 | 0.16124 | flat |
| race/gate_axis_x | -1.011976 | -1.033809 | flat |
| race/gate_centerline_dist | 0.748592 | 0.754422 | flat |
| race/obstacle_distance | 0.662054 | 0.67581 | flat |
| race/tilt_angle_deg | 20.803709 | 20.952051 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_015_stage2_no_wrappers_sensor15_curriculum_analysis.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_015_stage2_no_wrappers_sensor15_curriculum_analysis.json`
