# Level3 PPO Post-Run Analysis: level3_loop_015_structural_v5_localobs_remote_reward_30m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_015_structural_v5_localobs_remote_reward_30m/level3_loop_015_structural_v5_localobs_remote_reward_30m_step_015000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 95.00%
- Timeout rate: 5.00%
- Mean gates: 0.4
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': -0.05, 'crash_rate': 0.0, 'timeout_rate': 0.05, 'mean_gates': -0.55}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_015_structural_v5_localobs_remote_reward_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -10739.092773 | -15659.357747 | up |
| train/reward | -309.412628 | -42.626513 | down |
| losses/approx_kl | 0.001301 | 0.004698 | flat |
| losses/clipfrac | 0.000183 | 0.013782 | down |
| losses/entropy | 2.622119 | 2.517106 | up |
| losses/explained_variance | 0.671712 | 0.635551 | up |
| losses/value_loss | 175.979309 | 169.257095 | down |
| losses/policy_loss | -0.003105 | -0.004591 | flat |
| charts/SPS | 10844242.0 | 8621104.0 | up |
| race/passed_gate_rate | 0.006561 | 0.005636 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.011353 | 0.01179 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.300079 | 0.386353 | up |
| race/gate_axis_x | -0.808707 | -0.802443 | down |
| race/gate_centerline_dist | 0.695776 | 0.707414 | down |
| race/obstacle_distance | 0.601285 | 0.608957 | down |
| race/tilt_angle_deg | 15.642498 | 15.610353 | up |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_015_structural_v5_localobs_remote_reward_30m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_015_structural_v5_localobs_remote_reward_30m_analysis.json`
