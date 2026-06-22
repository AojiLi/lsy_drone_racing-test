# Level3 PPO Post-Run Analysis: level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m_final.ckpt`
- Success rate: 10.00%
- Mean successful time: 5.63
- Crash rate: 85.00%
- Timeout rate: 5.00%
- Mean gates: 1.4
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.1, 'crash_rate': -0.15, 'timeout_rate': 0.05, 'mean_gates': 0.55}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -210567.03125 | -200344.859375 | down |
| train/reward | -205.100769 | -419.456015 | down |
| losses/approx_kl | 0.000156 | 0.000314 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 9.791519 | 9.659991 | up |
| losses/explained_variance | 0.699485 | 0.696274 | up |
| losses/value_loss | 3735.734863 | 3651.232788 | up |
| losses/policy_loss | -0.000144 | -0.000494 | flat |
| charts/SPS | 6467410.0 | 5922681.0 | up |
| race/passed_gate_rate | 0.000305 | 0.000488 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.014679 | 0.014099 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.620789 | 0.602142 | up |
| race/gate_axis_x | -0.889756 | -0.88278 | up |
| race/gate_centerline_dist | 0.905617 | 0.890707 | up |
| race/gate_plane_dist | 0.906448 | 0.891301 | up |
| race/gate_plane_cross_rate | 0.006073 | 0.005386 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_036_structural_v5_decoupled_frame_clearance_low_pressure_reward_20m_analysis.json`
