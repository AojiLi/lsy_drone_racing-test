# Decision: Reject Plain v37 and Prepare v38 Retention

Decision: `launch_named_structural_lane`

Pending gate resolved by this packet:

- trial:
  `level3_loop_108_structural_v37b_residual_gru_mature_loop107_1m_2m`
- analysis:
  `experiments/level3_ppo_loop/analysis/level3_loop_108_structural_v37b_residual_gru_mature_loop107_1m_2m_analysis.md`
- subagent synthesis:
  `experiments/level3_ppo_loop/analysis/level3_loop_108_structural_v37b_residual_gru_mature_loop107_1m_2m_subagent_reviews.md`

Approved next lane:

```text
v38_gru_teacher_retention_distillation_from_loop107_1m
```

This is not a training command yet. It is a support/preflight implementation
lane before any long or short v38 training.

## Boundary

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization to make the metric easier.
- Do not continue plain v37/v37b.
- Do not start future training from loop108 checkpoints.
- Keep deployment as:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, rule controller, inference-time safety shield, or
upper-level controller is approved by this packet.

## Evidence

loop108 tested the approved short continuation from loop107 1M. It failed the
promotion rule.

Best loop108 checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_108_structural_v37b_residual_gru_mature_loop107_1m_2m/level3_loop_108_structural_v37b_residual_gru_mature_loop107_1m_2m_final.ckpt`
- success: `18/100`
- mean gates: `1.58`
- crash rate: `82%`
- mean successful time: `7.300s`

Dense loop108 milestones:

| Checkpoint | Success | Mean Gates | Crash | Mean Successful Time |
| --- | ---: | ---: | ---: | ---: |
| 0.5M | 11% | 1.50 | 89% | 7.258s |
| 1M | 17% | 1.55 | 83% | 7.141s |
| 1.5M | 13% | 1.39 | 87% | 7.346s |
| final | 18% | 1.58 | 82% | 7.300s |

Reference checkpoints:

- loop101 final: `20%` success, `1.69` mean gates, `80%` crash, `6.873s`;
- loop107 1M: `21%` success, `1.66` mean gates, `79%` crash, `7.578s`.

loop108 did not reproduce loop107 1M and did not beat loop101 on mean gates.

## Reviewer Synthesis

- Evaluator reviewer: reject plain v37/v37b. No loop108 checkpoint reaches
  loop107 1M or the loop101 gate frontier.
- W&B/PPO reviewer: this is not PPO instability. KL and clip fraction are tiny,
  entropy is flat, policy loss is near zero, and reward conversion failed.
  Retention metrics are inactive.
- Structure reviewer: retire plain v37 and prepare a named
  retention/distillation GRU lane from loop107 1M.

## Approved v38 Scope

`v38_gru_teacher_retention_distillation_from_loop107_1m`

Initial idea:

- Student start:
  loop107 1M residual-GRU checkpoint.
- Teacher/reference:
  a stable feed-forward frontier checkpoint, initially loop101 final unless
  later preflight evidence selects a better audited teacher.
- Train config:
  unchanged `config/level3.toml`.
- Hard eval config:
  unchanged `config/level3.toml`.
- Actor observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`.
- Controller:
  end-to-end PPO Actor only.
- Reward/PPO numbers:
  unchanged for the first v38 support screen.
- New requirement:
  explicit retention/distillation support with logged
  `teacher_kl`, `teacher_action_mse`, `teacher_agreement`, and sampled batch
  size greater than zero.

## Required Before Training

Do not launch v38 training until all of the following pass:

- teacher-retention dataset or online teacher sampling is implemented for
  residual-GRU students;
- source teacher checkpoint and observation layout are recorded in metadata;
- retention loss works with recurrent policy minibatches;
- metrics prove retention is active: nonzero sampled batch size and finite
  teacher KL/action MSE/agreement;
- deterministic or zero-update preflight confirms the student still loads from
  loop107 1M and teacher comparison is computed;
- dry-run shows v38 remains on unchanged `config/level3.toml`.

## Not Approved

- Do not continue loop108.
- Do not continue v37/v37b without retention.
- Do not tune reward numbers as the immediate next action.
- Do not tune PPO knobs silently.
- Do not change `config/level3.toml`.

## Promotion / Rejection Rule

After v38 support passes, run only a bounded screen with dense milestone evals.
Reject v38 if retention is not actually sampled/logged, or if hard eval remains
below `21%` success and `1.66` mean gates with contact-dominated failures.
