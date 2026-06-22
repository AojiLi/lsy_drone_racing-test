# Level3 PPO Post-Run Analysis: level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m_step_005000000.ckpt`
- Success rate: 10.00%
- Mean successful time: 6.67
- Crash rate: 90.00%
- Timeout rate: 0.00%
- Mean gates: 1.7
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.1, 'mean_time_s_success': -1.265, 'crash_rate': 0.1, 'timeout_rate': 0.0, 'mean_gates': 0.05}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -25793.3125 | -23372.669271 | down |
| train/reward | -146.338455 | -56.55818 | up |
| losses/approx_kl | 0.003252 | 0.003576 | flat |
| losses/clipfrac | 0.008167 | 0.009819 | flat |
| losses/entropy | 6.694512 | 6.658712 | up |
| losses/explained_variance | 0.772058 | 0.756102 | up |
| losses/value_loss | 570.572632 | 579.445089 | up |
| losses/policy_loss | -0.00325 | -0.003711 | flat |
| charts/SPS | 6481076.0 | 6229341.666667 | up |
| race/passed_gate_rate | 0.005829 | 0.005717 | flat |
| race/finished_rate | 0.0 | 7.1e-05 | flat |
| race/crashed_rate | 0.010559 | 0.009735 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.225983 | 0.216217 | up |
| race/gate_axis_x | -1.012046 | -1.004262 | up |
| race/gate_centerline_dist | 0.778281 | 0.765986 | flat |
| race/gate_plane_dist | 0.778547 | 0.76606 | flat |
| race/gate_plane_cross_rate | 0.003571 | 0.003225 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_077_structural_v21_default_gate_obstacle_frame_recovery_from_loop071_20m_analysis.json`
