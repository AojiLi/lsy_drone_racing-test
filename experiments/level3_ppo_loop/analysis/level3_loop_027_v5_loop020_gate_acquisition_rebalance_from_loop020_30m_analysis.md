# Level3 PPO Post-Run Analysis: level3_loop_027_v5_loop020_gate_acquisition_rebalance_from_loop020_30m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_027_v5_loop020_gate_acquisition_rebalance_from_loop020_30m/level3_loop_027_v5_loop020_gate_acquisition_rebalance_from_loop020_30m_final.ckpt`
- Success rate: 5.00%
- Mean successful time: 4.6
- Crash rate: 95.00%
- Timeout rate: 0.00%
- Mean gates: 0.8
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.05, 'crash_rate': -0.05, 'timeout_rate': 0.0, 'mean_gates': 0.75}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_027_v5_loop020_gate_acquisition_rebalance_from_loop020_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -73000.601562 | -72716.278646 | down |
| train/reward | -125.648514 | -98.045071 | down |
| losses/approx_kl | 3e-05 | 0.001637 | flat |
| losses/clipfrac | 0.0 | 0.000798 | flat |
| losses/entropy | 10.50848 | 10.380257 | up |
| losses/explained_variance | 0.756051 | 0.782125 | flat |
| losses/value_loss | 642.159058 | 550.209798 | down |
| losses/policy_loss | -0.000206 | -0.000602 | flat |
| charts/SPS | 10912465.0 | 10082409.333333 | up |
| race/passed_gate_rate | 0.001892 | 0.00177 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.015167 | 0.015045 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.446899 | 0.451304 | up |
| race/gate_axis_x | -0.761529 | -0.748603 | up |
| race/gate_centerline_dist | 0.854397 | 0.862727 | up |
| race/obstacle_distance | 0.604359 | 0.605744 | down |
| race/tilt_angle_deg | 18.975421 | 18.522696 | down |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_027_v5_loop020_gate_acquisition_rebalance_from_loop020_30m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_027_v5_loop020_gate_acquisition_rebalance_from_loop020_30m_analysis.json`
