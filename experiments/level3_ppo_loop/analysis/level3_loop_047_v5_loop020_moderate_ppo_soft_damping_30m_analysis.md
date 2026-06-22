# Level3 PPO Post-Run Analysis: level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m_final.ckpt`
- Success rate: 15.00%
- Mean successful time: 6.32
- Crash rate: 85.00%
- Timeout rate: 0.00%
- Mean gates: 1.25
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.05, 'mean_time_s_success': 0.37, 'crash_rate': -0.05, 'timeout_rate': 0.0, 'mean_gates': 0.2}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | 49145.5 | 43843.730469 | up |
| train/reward | 518.839844 | 134.205121 | up |
| losses/approx_kl | 0.000178 | 0.002984 | flat |
| losses/clipfrac | 0.0 | 0.003462 | flat |
| losses/entropy | 4.510735 | 4.49878 | down |
| losses/explained_variance | 0.765184 | 0.746685 | flat |
| losses/value_loss | 975.628174 | 959.99056 | up |
| losses/policy_loss | -0.00065 | -0.001723 | flat |
| charts/SPS | 10755579.0 | 9884665.666667 | up |
| race/passed_gate_rate | 0.010651 | 0.010091 | flat |
| race/finished_rate | 9.2e-05 | 0.000132 | flat |
| race/crashed_rate | 0.007507 | 0.008158 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.128174 | 0.135417 | down |
| race/gate_axis_x | -1.166958 | -1.112313 | down |
| race/gate_centerline_dist | 0.773259 | 0.763218 | flat |
| race/gate_plane_dist | 0.774197 | 0.76366 | flat |
| race/gate_plane_cross_rate | 0.002014 | 0.002533 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_047_v5_loop020_moderate_ppo_soft_damping_30m_analysis.json`
