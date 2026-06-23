# Level3 Framework Structural Update

Status: source-backed local synthesis for the post-loop098 stage.

Source: user-provided framework note from
`/home/aojili/.codex/attachments/a408143e-df22-4f76-87ad-dfe67c0b6b87/pasted-text-1.txt`.

## Decision Context

The final target is unchanged:

- hard eval on `config/level3.toml`;
- success rate `>= 0.60`;
- mean successful time `<= 7.0s`;
- no changes to Level3 track geometry or randomization to make the task easier.

Deployment must remain pure end-to-end PPO:

```text
Level3 observation/history
  -> PPO Actor
  -> roll / pitch / yaw / thrust
```

No MPC, waypoint planner, trajectory planner, or upper-level controller is
approved by this packet.

## Why Not Continue the Old Loop

The loop052/088/089/090-style family and the later longer-rollout maturation
family did not expand enough seed coverage. The pasted framework note estimates
that the old checkpoint family has only about 30/100 theoretical seed-union
coverage. Local loop098 evidence agrees with that diagnosis: continued v31d
maturation did not beat loop097's 20% success frontier.

v32 then tested the noisy-value hypothesis with an asymmetric privileged Critic.
Parity passed, but loop099 and loop100 did not beat loop097 on unchanged
`config/level3.toml`. loop100's best was only `19/100`, `1.65` mean gates, and
`81%` crash.

loop101 tested gate-phase reset curriculum. It tied the old success frontier at
`20/100`, reached `1.69` mean gates at final and `1.81` mean gates at 8M, but
did not reduce crash below `80/100`. loop106 then tested online
competence-gated level replay from loop101 and did not improve the frontier:
the best checkpoint only tied `20/100` success with lower `1.63` mean gates and
slower `7.744s` successful time, while final collapsed to `14/100`, `1.41`
mean gates, and `86%` crash. loop107 then tested residual-GRU transfer; its 1M
checkpoint reached `21/100` success, `1.66` mean gates, and `79%` crash, but
later checkpoints drifted down to `15/100`, `12/100`, `12/100`, and `17/100`.
loop108 then continued from loop107 1M and failed to reproduce the early
signal: best was only `18/100`, `1.58` mean gates, and `82%` crash.
Therefore the loop should stop treating reward-number tuning,
longer-rollout-only continuation, privileged-Critic maturation, v33 reset
curriculum, or MLP replay as the main bottleneck. The next bottleneck is likely
memory / partial observability plus retention against early-checkpoint drift.

## Structural Priority

Recommended order:

1. PPO correctness and reset/action semantics.
2. Clean longer-rollout feed-forward baseline.
3. Observation/return normalization support.
4. Asymmetric privileged Critic.
5. Gate-phase random reset / phase reset buffer.
6. Ability-gated curriculum.
7. Dynamic level sampling / prioritized level replay.
8. GRU only after reset semantics are proven clean.
9. Reward values after the training distribution and value signal are more
   trustworthy.
10. Speed pressure last.

## Immediate Lane

The current lane is:

```text
v38_gru_teacher_retention_distillation_from_loop107_1m
```

This lane is a support/preflight packet for explicit teacher retention or
distillation after plain v37/v37b failed to stabilize loop107 1M.

It keeps:

- `config/level3.toml` for training and hard eval;
- v5 deployed Actor observation;
- loop052 reward/PPO numbers;
- corrected v30 episode/reset/finish semantics;
- `256 envs x 128 steps`;
- no observation/return normalization.

It keeps the `mlp_residual_recurrent_actor_gru256` Actor structure and would
start from loop107 1M, not loop107 final. Do not launch training yet: v38 is
held until retention/distillation is implemented and tests prove nonzero
sampling plus finite teacher KL/action MSE/agreement logging. Do not repeat the
old from-scratch GRU lane.

## Deferred Work

Reward-number changes remain valid later stages, but they should not be
smuggled into v38. If retention/distillation cannot reproduce or improve the
21% / 1.66 frontier after support passes, retire GRU memory and move to a new
named structural direction rather than tuning this lane blindly.
