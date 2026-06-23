# Level3 PPO Post-Run Analysis: level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m

## Level3 Hard-Eval Scope

- Structural search is allowed only as an explicit named lane.
- Do not modify Level3 track geometry or randomization.
- Final acceptance must be hard eval on `config/level3.toml`.
- The main agent must write a decision packet before the next training chunk.
- Allowed next decisions: `stop_target_met`, `hold_for_more_analysis`, `continue_same_hypothesis`, `change_reward_or_training_numbers`, `launch_named_structural_lane`.

## Required Subagent Reviews

- `evaluator_metrics`: Audit checkpoint evidence from the hard evaluator. Focus on success rate, mean successful time, crashes, timeouts, gates, tilt, and whether any checkpoint is promising enough to mature.
- `wandb_ppo_diagnostics`: Audit W&B curves. Focus on train reward, reward components, race metrics, teacher-retention KL/agreement when present, value scale, value loss, KL, clip fraction, entropy, explained variance, SPS, and whether training signals convert into evaluator progress.
- `structure_research_synthesis`: Audit whether the failure is likely reward numbers, observation, controller wiring, reward structure, or training structure. Any framework change must be a named structural lane, source-backed when nontrivial, and must keep the Level3 target track unchanged.

## Evaluator Evidence

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m/level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m_step_004000000.ckpt`
- Success rate: 20.00%
- Mean successful time: 6.941
- Crash rate: 80.00%
- Timeout rate: 0.00%
- Mean gates: 1.6
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.2, 'crash_rate': 0.0, 'timeout_rate': -0.2, 'mean_gates': 1.54}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -4657.881348 | -4657.881348 | down |
| train/reward | -490.975708 | 2.850484 | down |
| losses/approx_kl | 4.2e-05 | 4.2e-05 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 4.481321 | 4.481321 | flat |
| losses/explained_variance | 0.761017 | 0.761017 | flat |
| losses/value_loss | 662.234924 | 662.234924 | flat |
| losses/policy_loss | -0.000191 | -0.000191 | flat |
| charts/SPS | 555219.0 | 555219.0 | up |
| losses/teacher_kl | 0.031987 | 0.031987 | flat |
| losses/teacher_action_mse | 0.005459 | 0.005459 | flat |
| retention/teacher_agreement | 0.94386 | 0.94386 | up |
| retention/sampled_batch_size | 512.0 | 512.0 | flat |
| race/passed_gate_rate | 0.005829 | 0.005829 | flat |
| race/finished_rate | 0.000244 | 0.000244 | flat |
| race/crashed_rate | 0.007172 | 0.007172 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.061066 | 0.061066 | flat |

## V27 Retention Evidence

| Metric | First | Last | Tail mean | Trend |
| --- | ---: | ---: | ---: | --- |
| losses/teacher_kl | 0.038228 | 0.031987 | 0.031987 | flat |
| losses/teacher_action_mse | 0.008527 | 0.005459 | 0.005459 | flat |
| retention/teacher_agreement | 0.909668 | 0.94386 | 0.94386 | up |
| retention/sampled_batch_size | 512.0 | 512.0 | 512.0 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_116_structural_v45_v5_frontier_union_retention_mlp_5m_analysis.json`
