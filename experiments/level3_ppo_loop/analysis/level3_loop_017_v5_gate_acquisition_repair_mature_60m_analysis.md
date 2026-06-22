# Level3 PPO Post-Run Analysis: level3_loop_017_v5_gate_acquisition_repair_mature_60m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_017_v5_gate_acquisition_repair_mature_60m/level3_loop_017_v5_gate_acquisition_repair_mature_60m_final.ckpt`
- Success rate: 5.00%
- Mean successful time: 5.26
- Crash rate: 95.00%
- Timeout rate: 0.00%
- Mean gates: 0.95
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'mean_time_s_success': -0.62, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.3}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_017_v5_gate_acquisition_repair_mature_60m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 15599.691406 | 18600.198568 | up |
| train/reward | -53.973835 | 79.502453 | up |
| losses/approx_kl | 0.006712 | 0.005862 | flat |
| losses/clipfrac | 0.018274 | 0.01485 | flat |
| losses/entropy | 3.518902 | 3.542088 | up |
| losses/explained_variance | 0.691919 | 0.706586 | flat |
| losses/value_loss | 659.223816 | 639.492249 | up |
| losses/policy_loss | -0.003464 | -0.002289 | flat |
| charts/SPS | 14463164.0 | 13193118.0 | up |
| race/passed_gate_rate | 0.009918 | 0.010376 | flat |
| race/finished_rate | 0.000244 | 0.000224 | flat |
| race/crashed_rate | 0.010559 | 0.010345 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.161774 | 0.16923 | flat |
| race/gate_axis_x | -0.969638 | -0.97275 | down |
| race/gate_centerline_dist | 0.721235 | 0.708417 | flat |
| race/obstacle_distance | 0.614984 | 0.631342 | flat |
| race/tilt_angle_deg | 17.529588 | 17.734598 | up |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_017_v5_gate_acquisition_repair_mature_60m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_017_v5_gate_acquisition_repair_mature_60m_analysis.json`
