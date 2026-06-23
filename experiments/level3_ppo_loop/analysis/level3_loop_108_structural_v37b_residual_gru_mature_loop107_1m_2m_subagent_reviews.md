# Subagent Reviews: loop108 v37b Residual-GRU 1M Maturation

Trial:
`level3_loop_108_structural_v37b_residual_gru_mature_loop107_1m_2m`

## Evaluator Metrics

Recommendation: reject plain v37 continuation and escalate to a new structural
lane.

- Best loop108 checkpoint is final: `18%` success, `1.58` mean gates,
  `82%` crash, `7.30s` mean successful time.
- Dense checkpoint sweep: `11%`, `17%`, `13%`, `18%` success.
- None reproduce loop107 1M: `21%` success, `1.66` mean gates, `79%` crash.
- None beat the loop101 gate frontier: `20%` success, `1.69` mean gates,
  `6.873s`.
- Do not start future training from loop108 checkpoints unless a later packet
  explicitly justifies it.

## W&B / PPO Diagnostics

Recommendation: do not continue loop108 or plain v37/v37b; do not silently tune
PPO knobs.

- This is not PPO instability: approximate KL is tiny, clip fraction is zero,
  entropy is flat, and policy loss is near zero.
- The pattern is no-conversion under-updating with weak retention.
- Value fit worsened: explained variance moved down and value loss moved up.
- Reward conversion failed: train reward and total reward moved down, passed
  gate and finish rates stayed flat, and crash remained high.
- Retention was inactive: `teacher_kl`, `teacher_action_mse`, and
  `retention/sampled_batch_size` are all zero.

## Structure / Research Synthesis

Recommendation: retire plain v37 and launch a named retention/distillation GRU
lane.

Proposed lane:

```text
v38_gru_teacher_retention_distillation_from_loop107_1m
```

Scope:

- Keep unchanged `config/level3.toml` for training and hard eval.
- Keep v5 observation layout.
- Keep PPO Actor-only deployment.
- Start from loop107 1M, the only useful GRU checkpoint.
- Add explicit teacher-retention/distillation metrics and tests before
  training; current retention metrics are inactive.

## Main-Agent Synthesis

Decision: `launch_named_structural_lane`, but held before training until v38
support exists.

Rationale:

- loop108 was the exact reproduction/maturation test requested by the loop107
  decision packet, and it failed.
- The failure is contact-dominated drift/no-conversion, not a reward-number
  justification.
- Plain residual-GRU continuation should stop.
- v38 should add retention/distillation explicitly, then run a bounded screen
  only after tests prove retention is sampled/logged.
