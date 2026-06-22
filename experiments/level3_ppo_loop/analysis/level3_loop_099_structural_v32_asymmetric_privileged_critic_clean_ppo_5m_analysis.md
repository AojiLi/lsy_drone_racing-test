# Level3 PPO Post-Run Analysis: level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_step_003000000.ckpt`
- Success rate: 19.00%
- Mean successful time: 7.2084210526315795
- Crash rate: 81.00%
- Timeout rate: 0.00%
- Mean gates: 1.66
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.0, 'mean_time_s_success': -0.287368, 'crash_rate': 0.0, 'timeout_rate': 0.0, 'mean_gates': 0.03}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -28444.457031 | -28444.457031 | flat |
| train/reward | -47.653667 | -122.571047 | up |
| losses/approx_kl | 6.7e-05 | 6.7e-05 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 4.194866 | 4.194866 | flat |
| losses/explained_variance | 0.763198 | 0.763198 | flat |
| losses/value_loss | 235.214935 | 235.214935 | flat |
| losses/policy_loss | -0.000528 | -0.000528 | flat |
| charts/SPS | 518991.0 | 518991.0 | up |
| losses/teacher_kl | 0.0 | 0.0 | flat |
| losses/teacher_action_mse | 0.0 | 0.0 | flat |
| retention/sampled_batch_size | 0.0 | 0.0 | flat |
| race/passed_gate_rate | 0.005798 | 0.005798 | flat |
| race/finished_rate | 0.000275 | 0.000275 | flat |
| race/crashed_rate | 0.006989 | 0.006989 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.066254 | 0.066254 | flat |
| race/gate_axis_x | -1.174724 | -1.174724 | flat |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_099_structural_v32_asymmetric_privileged_critic_clean_ppo_5m_analysis.json`
