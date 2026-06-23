# Level3 PPO Post-Run Analysis: level3_loop_103_structural_v35_competence_gated_curriculum_loop101_10m

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

- Best checkpoint: `lsy_drone_racing/control/checkpoints/level3_loop_103_structural_v35_competence_gated_curriculum_loop101_10m/level3_loop_103_structural_v35_competence_gated_curriculum_loop101_10m_step_009000000.ckpt`
- Success rate: 19.00%
- Mean successful time: 7.245263157894737
- Crash rate: 81.00%
- Timeout rate: 0.00%
- Mean gates: 1.68
- Target met: False
- Delta vs previous evaluated trial: `{'success_rate': 0.02, 'mean_time_s_success': -0.347678, 'crash_rate': -0.02, 'timeout_rate': 0.0, 'mean_gates': 0.09}`

## W&B Evidence

- Available: True
- Run URL: https://wandb.ai/aojili77-technical-university-of-munich/ADR-PPO-Racing-Level3/runs/level3_loop_103_structural_v35_competence_gated_curriculum_loop101_10m
- Reason if unavailable: None

| Metric | Last | Tail mean | Trend |
| --- | ---: | ---: | --- |
| train/total_reward | -29748.455078 | -29748.455078 | flat |
| train/reward | -147.036316 | -133.58046 | down |
| losses/approx_kl | 0.000546 | 0.000546 | flat |
| losses/clipfrac | 0.0 | 0.0 | flat |
| losses/entropy | 4.390876 | 4.390876 | flat |
| losses/explained_variance | 0.725929 | 0.725929 | flat |
| losses/value_loss | 271.61908 | 271.61908 | flat |
| losses/policy_loss | -0.000909 | -0.000909 | flat |
| charts/SPS | 1032972.0 | 1032972.0 | up |
| losses/teacher_kl | 0.0 | 0.0 | flat |
| losses/teacher_action_mse | 0.0 | 0.0 | flat |
| retention/sampled_batch_size | 0.0 | 0.0 | flat |
| race/passed_gate_rate | 0.005676 | 0.005676 | flat |
| race/finished_rate | 0.000458 | 0.000458 | flat |
| race/crashed_rate | 0.007416 | 0.007416 | flat |
| race/timeout_rate | 0.0 | 0.0 | flat |
| race/gate_stage | 0.074432 | 0.074432 | flat |
| race/gate_axis_x | -1.129161 | -1.129161 | up |

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
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_103_structural_v35_competence_gated_curriculum_loop101_10m_analysis.md \
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

- JSON snapshot: `experiments/level3_ppo_loop/analysis/level3_loop_103_structural_v35_competence_gated_curriculum_loop101_10m_analysis.json`
