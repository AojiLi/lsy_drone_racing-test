# Decision: Register Recurrent Actor GRU-256 Lane

## Decision

Register `v11_recurrent_actor_gru256_screen_from_scratch` as the next
memory-focused Level3 structural lane, but do not auto-launch it until the
trainer and inference controller implement recurrent PPO support.

## Context

- Current best checkpoint is loop052 with v5 local observation and 2x256 MLP:
  success_rate 0.20, mean_gates 1.4, mean successful time 6.975s.
- Loop060 v9 observation did not improve the best result.
- Hidden512 remains a cheap capacity ablation, but pure widening does not solve
  partial observability.
- Level3 uses randomized gates and obstacles with local sensing, so temporal
  memory is a stronger hypothesis than only increasing MLP width.

## Approved First GRU Screen

- Structural hypothesis:
  `v11_recurrent_actor_gru256_screen_from_scratch`
- Train/eval target:
  unchanged `config/level3_dr.toml`
- Actor observation:
  v5 local-obstacle observation, not v9
- Actor:
  FC128, FC128, GRU256, FC192, FC96, action mean 4 with Tanh
- Critic:
  same-observation 2x256 MLP for the first screen
- Sequence length:
  32 steps
- Training horizon:
  30M screening chunk with 5M checkpoint interval
- Evaluation:
  milestone-aware hard eval with the normal Level3 loop analyzer

## Explicit Non-Goals

- Do not modify Level3 track geometry or randomization.
- Do not label a normal MLP run as GRU.
- Do not add privileged Critic in the first GRU screen.
- Do not change reward structure at the same time as the first GRU screen.
- Do not use final checkpoint alone as the decision point.

## Implementation Requirement

Before this lane can train, implement recurrent PPO support in:

- `lsy_drone_racing/control/train_CleanRL_ppo_level3.py`
- `lsy_drone_racing/control/ppo_level3_inference.py`
- checkpoint metadata in `ppo_level3_observation.py` or equivalent helper
- loop/analyzer metadata so W&B and state identify the architecture

Until that implementation exists, the orchestrator should hold if this
hypothesis is explicitly requested and should skip it during automatic
structural search.

## Next Action

Keep the existing hidden512 ablation available. If hidden512 does not produce a
clear hard-eval improvement, implement recurrent PPO and dry-run:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --structural-hypothesis v11_recurrent_actor_gru256_screen_from_scratch \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop
```

