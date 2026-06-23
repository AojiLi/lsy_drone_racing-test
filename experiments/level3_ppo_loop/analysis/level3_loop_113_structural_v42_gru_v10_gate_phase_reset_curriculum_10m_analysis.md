# Level3 PPO Post-Run Analysis: level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m_step_004000000.ckpt`
- Success rate: 0.00%
- Mean successful time: None
- Crash rate: 54.00%
- Timeout rate: 46.00%
- Mean gates: 0.01
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'crash_rate': 0.02, 'timeout_rate': -0.02, 'mean_gates': 0.01}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -53541.269531 | -53541.269531 | up |
| train/reward | -236.414963 | -354.899112 | down |
| losses/approx_kl | 4.1e-05 | 4.1e-05 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 0.842345 | 0.842345 | up |
| losses/explained_variance | 0.037789 | 0.037789 | up |
| losses/value_loss | 736.193848 | 736.193848 | down |
| losses/policy_loss | -7.6e-05 | -7.6e-05 | flat |
| charts/SPS | 782009.0 | 782009.0 | up |
| losses/teacher_kl | 0.0 | 0.0 | flat |
| losses/teacher_action_mse | 0.0 | 0.0 | flat |
| retention/sampled_batch_size | 0.0 | 0.0 | flat |
| race/passed_gate_rate | 0.000214 | 0.000214 | flat |
| race/finished_rate | 0.0 | 0.0 | flat |
| race/crashed_rate | 0.004822 | 0.004822 | flat |
| race/timeout_rate | 9.2e-05 | 9.2e-05 | flat |
| race/gate_stage | 0.107391 | 0.107391 | up |
| race/gate_axis_x | -0.485916 | -0.485916 | up |

## V27 Retention Evidence

| Metric | First | Last | Tail mean | Trend |
| --- | ---: | ---: | ---: | --- |
| losses/teacher_kl | 0.0 | 0.0 | 0.0 | flat |
| losses/teacher_action_mse | 0.0 | 0.0 | 0.0 | flat |
| retention/sampled_batch_size | 0.0 | 0.0 | 0.0 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_113_structural_v42_gru_v10_gate_phase_reset_curriculum_10m_analysis.json`
