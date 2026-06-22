# Decision: Continue v31d to a 30M-Style Horizon

Decision: `continue_same_hypothesis`

Approved next lane:
`v31d_longer_rollout_maturation_from_loop097_12m_to_30m`

## Scope

- Final acceptance remains hard eval on unchanged `config/level3.toml`.
- Do not modify Level3 track geometry or randomization.
- Deployment remains end-to-end PPO actor to roll/pitch/yaw/thrust.
- Keep v5 observation, loop052 reward/PPO numbers, corrected v30 semantics, and
  no observation/return normalization.

## Evidence

loop097/v31d weakly improved the clean-PPO frontier:

- loop094/v31a best: `19/100` success, mean gates `1.55`, crash `81%`, mean
  successful time `6.8758s`.
- loop097/v31d best: `20/100` success, mean gates `1.66`, crash `80%`, mean
  successful time `7.055s`.
- loop097 best checkpoint:
  `lsy_drone_racing/control/checkpoints/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m_step_012000000.ckpt`.
- Target is not met: `20% < 60%`, and the best checkpoint is slightly slower
  than the `<=7.0s` time gate.

## Reviewer Synthesis

- Evaluator reviewer: continue from the 12M best checkpoint; the improvement is
  weak but positive enough under the step-curve rule.
- W&B/PPO reviewer: PPO is stable but quiet; conversion is weak, so a
  gate-acquisition reward adjustment is a reasonable fallback.
- Structure/research reviewer: continue to a 30M-style maturation before v32
  trainer-support work; promote toward 60M only if the frontier expands again.

## Next Lane

Run `v31d_longer_rollout_maturation_from_loop097_12m_to_30m`.

This lane:

- starts from loop097/v31d 12M best;
- adds 18M training steps, reaching a roughly 30M-style branch horizon;
- keeps all reward numbers unchanged;
- keeps `256 envs x 128 steps`;
- evaluates 3/6/9/12/15/18M continuation milestones on
  `config/level3.toml`.

## Fallback

If the 30M-style continuation does not beat `20%` success / `1.66` mean gates
or add meaningful new success seeds / lower crash, reject same-hypothesis
maturation and choose one of:

- a named gate-acquisition reward-number lane using the analyzer's proposed
  reward adjustment;
- v32 trainer-support work for asymmetric privileged critic, with tests and
  zero-update parity before training.

## Launch Command

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --max-iterations 1 \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --structural-hypothesis v31d_longer_rollout_maturation_from_loop097_12m_to_30m \
  --override-state-hold \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_097_structural_v31d_v31a_longer_rollout_maturation_15m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-22_level3_framework_structural_training_plan.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-22_loop097_continue_v31d_to_30m.md
```

