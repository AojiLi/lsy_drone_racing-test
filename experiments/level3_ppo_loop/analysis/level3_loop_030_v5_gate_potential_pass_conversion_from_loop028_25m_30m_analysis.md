# Level3 PPO Post-Run Analysis: level3_loop_030_v5_gate_potential_pass_conversion_from_loop028_25m_30m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_030_v5_gate_potential_pass_conversion_from_loop028_25m_30m/level3_loop_030_v5_gate_potential_pass_conversion_from_loop028_25m_30m_step_010000000.ckpt`
- Success rate: 5.00%
- Mean successful time: 6.02
- Crash rate: 95.00%
- Timeout rate: 0.00%
- Mean gates: 1.1
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.05, 'crash_rate': -0.05, 'timeout_rate': 0.0, 'mean_gates': 0.4}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_030_v5_gate_potential_pass_conversion_from_loop028_25m_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -100945.132812 | -99182.247396 | down |
| train/reward | -138.086655 | -178.063733 | down |
| losses/approx_kl | 8e-06 | 0.000198 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 16.70656 | 16.63357 | up |
| losses/explained_variance | 0.820459 | 0.82669 | up |
| losses/value_loss | 648.728638 | 583.307109 | up |
| losses/policy_loss | -0.000166 | -0.000624 | flat |
| charts/SPS | 10910648.0 | 10362293.333333 | up |
| race/passed_gate_rate | 0.000244 | 0.000254 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.015442 | 0.015127 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.624725 | 0.618398 | up |
| race/gate_axis_x | -0.753315 | -0.771447 | up |
| race/gate_centerline_dist | 0.964768 | 0.96675 | up |
| race/obstacle_distance | 0.615365 | 0.611367 | flat |
| race/tilt_angle_deg | 20.220841 | 20.007731 | up |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_030_v5_gate_potential_pass_conversion_from_loop028_25m_30m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_030_v5_gate_potential_pass_conversion_from_loop028_25m_30m_analysis.json`
