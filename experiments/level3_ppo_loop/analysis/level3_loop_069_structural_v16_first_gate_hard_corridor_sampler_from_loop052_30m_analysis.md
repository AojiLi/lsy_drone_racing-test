# Level3 PPO Post-Run Analysis: level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_step_025000000.ckpt`
- Success rate: 20.00%
- Mean successful time: 6.675000000000001
- Crash rate: 80.00%
- Timeout rate: 0.00%
- Mean gates: 1.45
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'mean_time_s_success': 0.055, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.2}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -32203.578125 | -32578.402344 | down |
| train/reward | -33.826874 | -121.824532 | up |
| losses/approx_kl | 0.003499 | 0.00452 | flat |
| losses/clipfrac | 0.007452 | 0.012216 | flat |
| losses/entropy | 5.147962 | 5.079235 | up |
| losses/explained_variance | 0.721404 | 0.758473 | flat |
| losses/value_loss | 253.558716 | 221.029865 | down |
| losses/policy_loss | -0.004225 | -0.005084 | flat |
| charts/SPS | 9933941.0 | 9118026.75 | up |
| race/passed_gate_rate | 0.00705 | 0.007034 | flat |
| race/finished_rate | 0.000244 | 0.000122 | flat |
| race/crashed_rate | 0.007843 | 0.007751 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.191925 | 0.199738 | up |
| race/gate_axis_x | -1.029888 | -1.038189 | up |
| race/gate_centerline_dist | 0.757031 | 0.748502 | flat |
| race/gate_plane_dist | 0.756748 | 0.748571 | flat |
| race/gate_plane_cross_rate | 0.002625 | 0.002594 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_069_structural_v16_first_gate_hard_corridor_sampler_from_loop052_30m_analysis.json`
