# Level3 PPO Post-Run Analysis: level3_loop_020_v5_completion_backloaded_from_loop019_15m

## Level3 Hard-Eval Scope

- Structural search is allowed only as an explicit named lane.
- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3_dr.toml`.
- The main agent must write a decision packet before the next training chunk.
- Allowed next decisions: `stop_target_met`, `hold_for_more_analysis`, `continue_same_hypothesis`, `change_reward_or_training_numbers`, `launch_named_structural_lane`.

## Required Subagent Reviews

- `evaluator_metrics`: Audit checkpoint evidence from the hard evaluator. Focus on success rate, mean successful time, crashes, timeouts, gates, tilt, and whether any checkpoint is promising enough to mature.
- `wandb_ppo_diagnostics`: Audit W&B curves. Focus on train reward, reward components, race metrics, value scale, value loss, KL, clip fraction, entropy, explained variance, SPS, and whether training signals convert into evaluator progress.
- `structure_research_synthesis`: Audit whether the failure is likely reward numbers, observation, controller wiring, reward structure, or training structure. Any framework change must be a named structural lane, source-backed when nontrivial, and must keep the Level3 target track unchanged.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_020_v5_completion_backloaded_from_loop019_15m/level3_loop_020_v5_completion_backloaded_from_loop019_15m_step_025000000.ckpt`
- Success rate: 15.00%
- Mean successful time: 6.366666666666667
- Crash rate: 85.00%
- Timeout rate: 0.00%
- Mean gates: 1.45
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.05, 'mean_time_s_success': 0.576667, 'crash_rate': -0.05, 'timeout_rate': 0.0, 'mean_gates': 0.3}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_020_v5_completion_backloaded_from_loop019_15m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 1498.55249 | 164.960022 | down |
| train/reward | -122.143921 | 5.322976 | up |
| losses/approx_kl | 8.8e-05 | 0.000117 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 5.09002 | 5.089505 | up |
| losses/explained_variance | 0.771838 | 0.769397 | up |
| losses/value_loss | 738.002319 | 720.877411 | down |
| losses/policy_loss | -0.000155 | -0.000492 | flat |
| charts/SPS | 10620840.0 | 10753827.0 | up |
| race/passed_gate_rate | 0.008331 | 0.008072 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.010071 | 0.009888 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.21109 | 0.205429 | up |
| race/gate_axis_x | -1.000085 | -1.018652 | up |
| race/gate_centerline_dist | 0.751532 | 0.756433 | flat |
| race/obstacle_distance | 0.67493 | 0.690463 | flat |
| race/tilt_angle_deg | 19.743625 | 19.753274 | flat |

## Diagnosis

- Branch: `gate_acquisition`
- Rationale: Low success with low mean gates points to gate acquisition.
- PPO instability metrics are diagnostics only; this loop must not tune `learning_rate`, `ent_coef`, `target_kl`, `update_epochs`, `num_minibatches`, `hidden_dim`, or `n_obs`.

## Parameter Recommendation

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_020_v5_completion_backloaded_from_loop019_15m_analysis.md \
  --param gate_stage_coef=13 \
  --param gate_axis_coef=24 \
  --param gate_front_bonus=5 \
  --param gate_bonus=200 \
  --param gate_back_bonus=35 \
  --param finish_bonus=175 \
  --param time_penalty=0.02
```

## Decision Gate

- Next training is blocked until the main agent synthesizes the analysis and subagent findings into a decision packet under `experiments/level3_ppo_loop/decisions/`.
- If the next move changes observation/controller/reward structure/PPO training structure, the packet must name the structural lane and cite the local or external evidence.

## Artifacts

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_020_v5_completion_backloaded_from_loop019_15m_analysis.json`
