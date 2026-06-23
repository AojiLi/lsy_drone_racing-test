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

Therefore the loop should stop treating reward-number tuning, seed replay,
longer-rollout-only continuation, and privileged-Critic maturation as the main
bottleneck. The next bottleneck is likely training distribution: the policy
does not see enough useful gate approach/pass/exit states.

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
v33_gate_phase_reset_curriculum_from_loop097_12m
```

This lane is a bounded 10M training screen from the loop097/v31d 12M checkpoint.

It keeps:

- `config/level3.toml` for training and hard eval;
- v5 deployed Actor observation;
- loop052 reward/PPO numbers;
- corrected v30 episode/reset/finish semantics;
- `256 envs x 128 steps`;
- no observation/return normalization.

It changes only the training reset distribution:

- 45% of episodes reset near randomized target-gate approach phases;
- 55% of episodes keep normal Level3 starts.

## Deferred Work

Competence-gated curriculum, PLR, GRU, and reward-number changes remain valid
next stages, but they should be separate named lanes with their own packets and
hard-eval analysis. They should not be smuggled into v33.
