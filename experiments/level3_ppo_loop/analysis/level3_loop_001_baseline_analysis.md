# Level3 PPO Post-Run Analysis: level3_loop_001_baseline

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_001_baseline/level3_loop_001_baseline_final.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 100.00%
- Timeout rate: 0.00%
- Mean gates: 0.85
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.0}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_001_baseline
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -8304.962891 | -8933.624023 | up |
| train/reward | -179.704895 | -49.770271 | down |
| losses/approx_kl | 0.002649 | 0.003219 | flat |
| losses/clipfrac | 0.002686 | 0.005051 | flat |
| losses/entropy | 4.819009 | 4.809078 | down |
| losses/explained_variance | 0.712551 | 0.730147 | flat |
| losses/value_loss | 344.295074 | 341.027786 | up |
| losses/policy_loss | -0.005356 | -0.005473 | flat |
| charts/SPS | 7161687.0 | 6640275.0 | up |
| race/passed_gate_rate | 0.007843 | 0.007736 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.012604 | 0.012238 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.218323 | 0.224594 | down |
| race/gate_axis_x | -0.871076 | -0.869575 | down |
| race/gate_centerline_dist | 0.740933 | 0.746865 | flat |
| race/obstacle_distance | 0.607566 | 0.60969 | flat |
| race/tilt_angle_deg | 20.226528 | 20.134169 | flat |

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
  --research-packet experiments/level3_ppo_loop/analysis/level3_loop_001_baseline_analysis.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_001_baseline_analysis.json`
