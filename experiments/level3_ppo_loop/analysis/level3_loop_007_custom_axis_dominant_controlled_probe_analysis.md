# Level3 PPO Post-Run Analysis: level3_loop_007_custom_axis_dominant_controlled_probe

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_007_custom_axis_dominant_controlled_probe/level3_loop_007_custom_axis_dominant_controlled_probe_final.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.75
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.05}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_007_custom_axis_dominant_controlled_probe
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 528.322266 | 923.649902 | down |
| train/reward | 100.494331 | -7.323056 | up |
| losses/approx_kl | 0.000373 | 0.000535 | flat |
| losses/clipfrac | 0.0 | 4.3e-05 | flat |
| losses/entropy | 5.51513 | 5.512891 | up |
| losses/explained_variance | 0.76131 | 0.747975 | up |
| losses/value_loss | 746.188477 | 726.651489 | up |
| losses/policy_loss | -0.001095 | -0.001542 | flat |
| charts/SPS | 11792547.0 | 11563843.666667 | up |
| race/passed_gate_rate | 0.008087 | 0.008525 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.010956 | 0.012105 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.246521 | 0.236928 | up |
| race/gate_axis_x | -0.857041 | -0.862452 | flat |
| race/gate_centerline_dist | 0.72399 | 0.737723 | flat |
| race/obstacle_distance | 0.611255 | 0.623481 | flat |
| race/tilt_angle_deg | 20.235292 | 20.14562 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_007_custom_axis_dominant_controlled_probe_analysis.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_007_custom_axis_dominant_controlled_probe_analysis.json`
