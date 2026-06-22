# Level3 PPO Post-Run Analysis: level3_loop_002_gate_acquisition_safety

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_002_gate_acquisition_safety/level3_loop_002_gate_acquisition_safety_step_010000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.8
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': -0.05}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_002_gate_acquisition_safety
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -919.221252 | -1192.292389 | up |
| train/reward | 11.489281 | -0.237259 | up |
| losses/approx_kl | 9.3e-05 | 0.000323 | flat |
| losses/clipfrac | 0.0 | 9e-06 | flat |
| losses/entropy | 5.024626 | 5.023614 | up |
| losses/explained_variance | 0.739566 | 0.740387 | flat |
| losses/value_loss | 521.828674 | 532.383087 | up |
| losses/policy_loss | -0.000479 | -0.001497 | flat |
| charts/SPS | 8360563.0 | 8061222.5 | up |
| race/passed_gate_rate | 0.009369 | 0.009293 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.011719 | 0.011703 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.212006 | 0.203201 | flat |
| race/gate_axis_x | -0.869556 | -0.874173 | flat |
| race/gate_centerline_dist | 0.730639 | 0.73621 | down |
| race/obstacle_distance | 0.613139 | 0.609776 | flat |
| race/tilt_angle_deg | 19.403233 | 19.37194 | down |

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
  --research-packet experiments/level3_ppo_loop/analysis/level3_loop_002_gate_acquisition_safety_analysis.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_002_gate_acquisition_safety_analysis.json`
