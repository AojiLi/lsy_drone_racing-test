# Level3 PPO Post-Run Analysis: level3_loop_010_stage2_no_train_wrappers

## Locked Scope

- Reward-only tuning.
- Do not change PPO hyperparameters, algorithm, observation layout, network/training structure, curriculum, or add reward channels.
- Disabled reward channels stay at zero: `progress_coef`, `near_gate_coef`, `gate_plane_bonus`, `missed_gate_penalty`, `obstacle_clearance_coef`.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_010_stage2_no_train_wrappers/level3_loop_010_stage2_no_train_wrappers_step_015000000.ckpt`
- Success rate: 5.00%
- Mean successful time: 5.64
- Crash rate: 95.00%
- Timeout rate: 0.00%
- Mean gates: 0.8
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.05, 'crash_rate': -0.05, 'timeout_rate': 0.0, 'mean_gates': 0.05}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_010_stage2_no_train_wrappers
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 20578.628906 | 21362.502604 | up |
| train/reward | -111.28009 | 61.238686 | up |
| losses/approx_kl | 3.2e-05 | 0.001176 | flat |
| losses/clipfrac | 0.0 | 0.000798 | flat |
| losses/entropy | 4.798872 | 4.791863 | flat |
| losses/explained_variance | 0.81404 | 0.794106 | up |
| losses/value_loss | 537.742676 | 599.656657 | down |
| losses/policy_loss | -0.000342 | -0.000235 | flat |
| charts/SPS | 15832939.0 | 15073848.0 | up |
| race/passed_gate_rate | 0.009857 | 0.010132 | flat |
| race/finished_rate | 0.0 | 2e-05 | flat |
| race/crashed_rate | 0.010315 | 0.010376 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.199249 | 0.187083 | down |
| race/gate_axis_x | -0.990413 | -0.994326 | down |
| race/gate_centerline_dist | 0.715187 | 0.726365 | flat |
| race/obstacle_distance | 0.646244 | 0.649335 | flat |
| race/tilt_angle_deg | 19.497015 | 19.644043 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_010_stage2_no_train_wrappers_analysis.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_010_stage2_no_train_wrappers_analysis.json`
