# Decision: Reject v31d Maturation and Prepare v32 Privileged Critic

Decision: `launch_named_structural_lane`

Approved next lane:
`v32_asymmetric_privileged_critic_support_parity`

This is a support/parity lane, not a training launch. Do not start the next PPO
training run until the v32 support packet is implemented and zero-update actor
parity passes.

## Scope

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry or randomization.
- Deployed inference remains the existing v5 observation/history actor path:
  `Level3 observation/history -> PPO actor -> roll/pitch/yaw/thrust`.
- Privileged/full-track state may be used only by the Critic during training.
- Actor inputs, action semantics, and evaluator inference must remain unchanged
  unless a later explicitly approved structural lane says otherwise.

## Evidence

loop098 matured the loop097/v31d 12M best checkpoint by 18M additional steps,
reaching a roughly 30M-style branch horizon. It did not expand the frontier.

Best loop098 checkpoint:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_098_structural_v31d_longer_rollout_mature_loop097_12m_to_30m/level3_loop_098_structural_v31d_longer_rollout_mature_loop097_12m_to_30m_step_012000000.ckpt`
- success: `19/100`
- mean successful time: `7.496s`
- crash rate: `81%`
- timeout rate: `0%`
- mean gates: `1.63`

Global best remains loop097:

- checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m_step_012000000.ckpt`
- success: `20/100`
- mean successful time: `7.055s`
- crash rate: `80%`
- timeout rate: `0%`
- mean gates: `1.66`

Milestone scan for loop098:

| Checkpoint | Success | Mean Time | Crash | Mean Gates |
| --- | ---: | ---: | ---: | ---: |
| 3M | 10% | 7.382s | 90% | 1.45 |
| 6M | 17% | 7.219s | 83% | 1.66 |
| 9M | 14% | 6.970s | 86% | 1.41 |
| 12M | 19% | 7.496s | 81% | 1.63 |
| 15M | 14% | 6.926s | 86% | 1.62 |
| 16M | 18% | 6.986s | 82% | 1.67 |
| 17M | 16% | 6.877s | 84% | 1.61 |
| final | 14% | 7.401s | 86% | 1.51 |

## Reviewer Synthesis

- Evaluator reviewer: loop098 regressed versus loop097; do not continue v31d
  maturation.
- W&B/PPO reviewer: PPO metrics look stable, but training signals did not
  convert into evaluator progress. This is plateau, not an obvious PPO blow-up.
- Structure/research reviewer: switch to a named structural lane, specifically
  asymmetric privileged Critic support with parity checks before any training.

## Next Work

Implement and validate `v32_asymmetric_privileged_critic_support_parity`.

Required before training:

1. Add trainer/checkpoint metadata support for an asymmetric Critic that can
   receive training-only privileged/full-state observations.
2. Keep Actor observations and evaluator inference byte-for-byte compatible with
   the deployed v5 actor path.
3. Add tests or deterministic checks proving:
   - Actor checkpoint load parity against loop097/v31d 12M best.
   - Zero-update actor outputs are unchanged after introducing Critic-only
     privileged-state plumbing.
   - Evaluation on `validation_unseen_101_200` still reproduces the loop097
     12M checkpoint frontier within expected deterministic tolerance before any
     v32 training.
4. Only after parity passes, add a bounded training lane such as
   `v32_asymmetric_privileged_critic_clean_ppo_5m` with milestone hard eval on
   unchanged `config/level3.toml`.

## Training Hold

No next training command is approved by this packet. The next Codex action is
implementation and deterministic parity validation for v32 support.
