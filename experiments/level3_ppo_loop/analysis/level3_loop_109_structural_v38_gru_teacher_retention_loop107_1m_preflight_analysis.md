# Level3 PPO Post-Run Analysis: level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight_step_001000000.ckpt`
- Success rate: 18.00%
- Mean successful time: 6.844444444444445
- Crash rate: 82.00%
- Timeout rate: 0.00%
- Mean gates: 1.64
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'mean_time_s_success': -0.455556, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.06}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -34522.988281 | -34522.988281 | down |
| train/reward | -303.706421 | -107.955494 | down |
| losses/approx_kl | 0.000681 | 0.000681 | flat |
| losses/clipfrac | 6e-06 | 6e-06 | flat |
| losses/entropy | 4.335754 | 4.335754 | flat |
| losses/explained_variance | 0.75481 | 0.75481 | flat |
| losses/value_loss | 234.153534 | 234.153534 | down |
| losses/policy_loss | -0.000733 | -0.000733 | flat |
| charts/SPS | 159777.0 | 159777.0 | up |
| losses/teacher_kl | 0.009628 | 0.009628 | flat |
| losses/teacher_action_mse | 0.001754 | 0.001754 | flat |
| retention/teacher_agreement | 0.989709 | 0.989709 | up |
| retention/sampled_batch_size | 512.0 | 512.0 | flat |
| race/passed_gate_rate | 0.005707 | 0.005707 | flat |
| race/finished_rate | 0.000122 | 0.000122 | flat |
| race/crashed_rate | 0.007721 | 0.007721 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.062683 | 0.062683 | flat |

## V27 Retention Evidence

| Metric | First | Last | Tail mean | Trend |
| --- | ---: | ---: | ---: | --- |
| losses/teacher_kl | 0.019012 | 0.009628 | 0.009628 | flat |
| losses/teacher_action_mse | 0.004303 | 0.001754 | 0.001754 | flat |
| retention/teacher_agreement | 0.952258 | 0.989709 | 0.989709 | up |
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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_109_structural_v38_gru_teacher_retention_loop107_1m_preflight_analysis.json`
