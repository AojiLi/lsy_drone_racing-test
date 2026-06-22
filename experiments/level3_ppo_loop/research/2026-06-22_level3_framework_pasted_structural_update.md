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

Therefore the loop should stop treating reward-number tuning and seed replay as
the main bottleneck. The next bottleneck is likely noisy value/advantage
estimation under partial Actor observability.

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
v32_asymmetric_privileged_critic_support_parity
```

This lane is implementation plus parity only. It does not approve training by
itself.

Required support:

- Actor observes exactly the deployed v5 observation/history prefix.
- Critic may receive a training-only privileged tail containing full-track state.
- Checkpoints record `critic_observation_mode`, `actor_observation_dim`, and
  `critic_observation_dim`.
- Inference ignores Critic-only privileged weights and loads the Actor path
  exactly as before.
- A zero-update v32 checkpoint generated from loop097/v31d 12M must reproduce
  deterministic `validation_unseen_101_200` hard-eval behavior before any v32
  training launch.

## First Training Lane After Parity

After parity passes, the bounded first training lane is:

```text
v32_asymmetric_privileged_critic_clean_ppo_5m
```

It keeps:

- `config/level3.toml` for training and hard eval;
- v5 deployed Actor observation;
- loop052 reward/PPO numbers;
- corrected v30 episode/reset/finish semantics;
- `256 envs x 128 steps`;
- no observation/return normalization in the first asymmetric Critic pass.

It changes only:

- Critic input mode from `same_as_actor` to `level3_full_state_v1`.

## Deferred Work

Gate-phase resets, curriculum, PLR, GRU, and reward-number changes remain valid
next stages, but they should be separate named lanes with their own packets and
hard-eval analysis. They should not be smuggled into v32.
