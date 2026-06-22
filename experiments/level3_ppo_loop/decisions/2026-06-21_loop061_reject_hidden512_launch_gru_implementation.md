# Loop061 Decision: Reject Hidden512 Continuation, Implement GRU Lane

## Decision

`launch_named_structural_lane`

Implement the recurrent PPO support required for
`v11_recurrent_actor_gru256_screen_from_scratch`, then dry-run that lane before
any GRU training.

## Hard Boundary

- Target hard eval remains `config/level3_dr.toml`.
- Do not modify Level3 track geometry, gate layout, obstacle layout, or
  randomization.
- Do not accept any result unless it is hard-evaluated on the unchanged Level3
  target track.

## Evidence

Loop061 tested the hidden512 capacity ablation:

- Proposal:
  `structural_v10_hidden512_warmstart_capacity_from_loop052_30m`
- Observation layout:
  `level3_gate_aperture_margin_2obs_local_history_v9`
- Network:
  2x512 Tanh MLP Actor/Critic, warm-started from loop052
- Best checkpoint:
  `level3_loop_061_structural_v10_hidden512_warmstart_capacity_from_loop052_30m_step_020000000.ckpt`
- Best hard eval:
  - success_rate: 0.10
  - crash_rate: 0.90
  - mean_gates: 1.10
  - mean successful time: 6.40s

Global best remains loop052:

- success_rate: 0.20
- crash_rate: 0.80
- mean_gates: 1.40
- mean successful time: 6.975s

Loop061 therefore failed both promotion gates from the hidden512 decision
packet: it did not exceed loop052's 20% success rate and did not materially
improve beyond 1.4 mean_gates.

## Subagent Synthesis

- Evaluator reviewer:
  reject hidden512 maturation. The 20M checkpoint is best within loop061 but
  regresses by 10 percentage points success, increases crash by 10 percentage
  points, and loses 0.30 mean_gates versus loop052.
- W&B/PPO reviewer:
  no PPO collapse, but KL and clipfrac are very low. Training shows small
  shaped-reward movement without race conversion; passed-gate, finish, gate
  stage, and plane-crossing signals stay flat.
- Structure/research reviewer:
  reject hidden512 as a continued structural lane. The failure mode is better
  explained by partial observability and lack of temporal memory than by
  insufficient MLP width.

## Next Move

Do not continue hidden512 to 60M/90M. Do not start
`v10_hidden512_reward_search_from_best` as the next move.

Instead, implement recurrent PPO support for the already registered lane:

`v11_recurrent_actor_gru256_screen_from_scratch`

First GRU screen contract:

- Actor observation:
  `level3_target_gate_nearest_gate_2obs_local_history_v5`
- Actor:
  FC128 + Tanh, FC128 + Tanh, GRU256, FC192 + Tanh, FC96 + Tanh,
  action mean 4 + Tanh, learned log_std[4]
- Critic:
  same actor observation, 2x256 Tanh MLP
- Sequence length:
  32 steps
- Reset recurrent state on episode termination/truncation
- No privileged Critic in this first GRU screen
- No simultaneous reward-structure change
- Hard eval:
  unchanged `config/level3_dr.toml`

## Required Implementation Before Training

- Recurrent Actor module and checkpoint metadata.
- PPO rollout storage for recurrent hidden states and done masks.
- Sequence-aware PPO minibatches.
- Inference controller hidden-state maintenance and reset handling.
- Loop/analyzer metadata showing the training structure.
- Dry-run of:

```bash
pixi run -e gpu python scripts/level3_ppo_loop.py \
  --dry-run \
  --structural-hypothesis v11_recurrent_actor_gru256_screen_from_scratch \
  --wandb-enabled \
  --wandb-entity aojili77-technical-university-of-munich \
  --codex-autonomous-loop \
  --analysis-packet experiments/level3_ppo_loop/analysis/level3_loop_061_structural_v10_hidden512_warmstart_capacity_from_loop052_30m_analysis.md \
  --research-packet experiments/level3_ppo_loop/research/2026-06-21_recurrent_actor_gru256_strategy.md \
  --approved-hypothesis-packet experiments/level3_ppo_loop/decisions/2026-06-21_loop061_reject_hidden512_launch_gru_implementation.md
```

