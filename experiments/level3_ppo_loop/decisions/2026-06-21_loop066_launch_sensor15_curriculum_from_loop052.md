# Loop066 Decision: Launch Sensor15 Curriculum From Loop052

## Decision

`launch_named_structural_lane`

Launch:

`v15_loop052_sensor15_curriculum_nominal_reward`

This packet resolves the post-run decision gate for:

- trial_id:
  `level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m`
- analysis_report:
  `experiments/level3_ppo_loop/analysis/level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m_analysis.md`
- analysis_json:
  `experiments/level3_ppo_loop/analysis/level3_loop_066_structural_v14_mlp_loop052_constant_lr_directional_pass_conversion_guard_20m_analysis.json`

## Hard Boundary

- Target hard eval remains `config/level3_dr.toml`.
- Do not modify Level3 target track geometry, gate layout, obstacle layout, or
  randomization.
- The training-only curriculum may change training sensor visibility, but the
  accepted checkpoint must be evaluated on unchanged `config/level3_dr.toml`.

## Evidence

Loop066 tested the v14 directional pass-conversion guard and did not beat the
global-best loop052 checkpoint:

| Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| loop052 final | 0.20 | 1.40 | 0.80 | 6.975s |
| loop065 final | 0.15 | 1.25 | 0.85 | 6.393s |
| loop066 10M | 0.10 | 1.25 | 0.90 | 6.400s |

The trace-axis synthesis is:

`experiments/level3_ppo_loop/research/2026-06-21_loop066_trace_axis_synthesis.md`

It identifies the next useful axis as `curriculum/seed-geometry triage`, not
another immediate reward-only pass, hidden512 continuation, GRU maturation, or
controller smoothing lane.

## Lane Contract

Name:

`v15_loop052_sensor15_curriculum_nominal_reward`

Run proposal:

`structural_v15_loop052_sensor15_curriculum_nominal_reward_20m`

Training config:

`config/level3_dr_stage2_gate0_sensor15.toml`

Hard eval config:

`config/level3_dr.toml`

Initial checkpoint:

`lsy_drone_racing/control/checkpoints/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m/level3_loop_052_v5_remote_safer_anchor_nominal_reward_dr_30m_final.ckpt`

Observation:

`level3_target_gate_nearest_gate_2obs_local_history_v5`

Actor/Critic:

- 2x256 Tanh MLP Actor
- 2x256 Tanh MLP Critic
- no GRU in this lane
- no privileged Critic in this lane

Training numbers:

- `learning_rate=5e-5`
- `anneal_lr=False`
- 20M screening chunk
- 5M checkpoint interval

Reward numbers:

Use loop052 nominal reward numbers, not v13/v14 aggressive gate-pressure
numbers.

## Difference From Failed Curriculum Lanes

This is not a repeat of loop032:

- loop032 used `level3_dr_stage2_no_train_wrappers.toml`;
- this lane keeps the train wrappers and deploy-style robustness stack;
- loop032 removed robustness pressure and produced severe command saturation;
- this lane changes only training sensor visibility to help route learning.

This is also not a repeat of the early sensor15 probe:

- the early probe started from weaker older checkpoints and older observation
  assumptions;
- this lane starts from loop052, the current global-best hard-eval checkpoint;
- this lane keeps v5 local-obstacle observation and loop052 nominal reward.

## Promotion Rule

Promote the same lane toward 60M/90M only if any milestone checkpoint has:

- `success_rate > 0.20`, or
- `mean_gates > 1.45`, or
- `success_rate == 0.20` with `mean_gates > 1.40` and `crash_rate <= 0.80`,
  plus W&B pass/finish/plane-cross curves that improve versus loop052/v14.

## Rejection Rule

Reject this lane if all milestone checkpoints stay at or below:

- `success_rate <= 0.15`, or
- `mean_gates <= 1.30`, or
- `crash_rate >= 0.85`,

especially if W&B race conversion remains flat or trace analysis shows the
same hard seeds failing without improved route progress.

## Required Post-Run Work

After the train/evaluate chunk:

1. Run `scripts/analyze_level3_ppo_trial.py`.
2. Use exactly three review roles: evaluator metrics, W&B/PPO diagnostics, and
   structure/research synthesis.
3. Write a new main-agent decision packet before launching another training
   chunk.
